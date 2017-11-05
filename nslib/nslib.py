import requests
import base64
import uuid
import datetime

from cachetools import cached, TTLCache

from data.stations import STATIONS
from nsexceptions import (ConnectionError, InvalidCredentials, InvalidCard, TooManyRequests)

CACHE_SECONDS = 240

state_cache = TTLCache(maxsize=1, ttl=CACHE_SECONDS)

class NsCard(object):
    def __init__(self, number, headers):
        self.number = number

        self._CID = None
        self._headers = headers

        self._fetchCID()

    def _fetchCID(self):
        headers = self._headers
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        try:
            rCID = requests.post("https://ews-rpx.ns.nl/private-reistransacties-api/service/selectcard/" + str(self.number), headers=headers)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to NS servers.")

        if "Minimum request interval exceeded" in rCID.text:
            raise TooManyRequests("Minimum request interval exceeded.")

        self._CID = rCID.json()["cid"]

    @property
    @cached(state_cache)
    def _state(self):
        headers = {
                "Accept": self._headers["Accept"],
                "Accept-Encoding": "gzip",
                "X-Request-ID": str(uuid.uuid4()),
                "Authorization": self._headers["Authorization"],
                "User-Agent": "rpx_android/5.0.14:519",
                "connection": "Keep-Alive",
                "Host": self._headers["Host"],
                "content-length": self._headers["content-length"]
        }

        try:
            rCard = requests.get("https://ews-rpx.ns.nl/private-reistransacties-api/service/transactions/" + self._CID, headers=headers)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to NS servers.")

        cardData = rCard.json()

        stateObject = {
            "checkedIn": False,
            "trips": []
        }

        if len(cardData["transactions"]) > 0:
            stateObject["balance"] = cardData["transactions"][0]["remainingPurseValue"]

            for transaction in cardData["transactions"]:
                trip = {
                    "balance": transaction["remainingPurseValue"]
                }

                trip["arrival"] = STATIONS[transaction["arrival"]["station"]["stationCode"]]
                trip["arrival"]["stationCode"] = transaction["arrival"]["station"]["stationCode"]
                trip["arrival"]["time"] = datetime.datetime.strptime(transaction["arrival"]["timestamp"], "%d-%m-%Y %H:%M:%S +01:00")

                trip["departure"] = STATIONS[transaction["departure"]["station"]["stationCode"]]
                trip["departure"]["stationCode"] = transaction["departure"]["station"]["stationCode"]
                trip["departure"]["time"] = datetime.datetime.strptime(transaction["departure"]["timestamp"], "%d-%m-%Y %H:%M:%S +01:00")

                stateObject["trips"].append(trip)

        return stateObject

    @property
    def checkedIn(self):
        return self._state["checkedIn"]

    @property
    def balance(self):
        if "balance" in self._state:
            return self._state["balance"]
        else:
            return None

    @property
    def trips(self):
        return self._state["trips"]

class NsAccount(object):
    def __init__(self, username, password):
        self.user = username
        self.password = username
        self.cards = []

        self._bearer = base64.b64encode((username + ":" + password).encode("ascii")).decode("ascii")
        self._headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip,deflate,sdch",
            "User-Agent": "Google-HTTP-Java-Client/1.19.0 (gzip)",
            "connection": "Close",
            "Host": "ews-rpx.ns.nl",
            "content-length": "0"
        }

        self._login()

    def _login(self):
        self._headers["Authorization"] = "Basic " + self._bearer

        try:
            rLogin = requests.get("https://ews-rpx.ns.nl/private-reistransacties-api/service/cards", headers=self._headers)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to NS servers.")

        if "401 Unauthorized" in rLogin.text:
            raise InvalidCredentials("The username or password are invalid.")

        for card in rLogin.json()["cards"]:
            self.cards.append(NsCard(card["ovcpNumber"], self._headers))
