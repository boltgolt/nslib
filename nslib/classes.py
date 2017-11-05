import requests
import base64
import uuid
import datetime

from cachetools import cached, TTLCache

from .stations import STATIONS
from .nsexceptions import ConnectionError, InvalidCredentials, InvalidCard, TooManyRequests

CARD_CACHE_SEC = 240

class Card(object):
    """Representation of a single ov-chipcard."""

    def __init__(self, number, headers):
        self.number = number

        self._CID = None
        self._headers = headers

        self._fetchCID()

    def _fetchCID(self):
        """Fetch CID token from NS servers for later use"""
        headers = self._headers
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        try:
            rCID = requests.post("https://ews-rpx.ns.nl/private-reistransacties-api/service/selectcard/" + str(self.number), headers=headers)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to NS servers.")

        # This endpoint is strictly rate limited, this error will solve itself in a minute or 2
        if "Minimum request interval exceeded" in rCID.text:
            raise TooManyRequests("Minimum request interval exceeded.")

        self._CID = rCID.json()["cid"]

    @property
    @cached(TTLCache(maxsize=1, ttl=CARD_CACHE_SEC))
    def _state(self):
        """Update the last known state of the card."""
        headers = {
                "Accept": self._headers["Accept"],
                "Accept-Encoding": "gzip",
                # The original API request used UUIDv1, but we use UUIDv4 for simplicity
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
        """Return check-in status and update if needed"""
        return self._state["checkedIn"]

    @property
    def balance(self):
        """Return balance if available and update if needed"""
        if "balance" in self._state:
            return self._state["balance"]
        else:
            return None

    @property
    def trips(self):
        """Return last known trips and update if needed"""
        return self._state["trips"]

class Account(object):
    """Representation of a NS online account."""
    def __init__(self, username, password):
        self.user = username
        self.password = username
        self.cards = []

        # The bearer token is a simple USER:PASS string encoded in base64
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
        """Authenticate with the NS servers."""
        self._headers["Authorization"] = "Basic " + self._bearer

        try:
            rLogin = requests.get("https://ews-rpx.ns.nl/private-reistransacties-api/service/cards", headers=self._headers)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to NS servers.")

        if "401 Unauthorized" in rLogin.text:
            raise InvalidCredentials("The username or password are invalid.")

        for card in rLogin.json()["cards"]:
            self.cards.append(Card(card["ovcpNumber"], self._headers))
