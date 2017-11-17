"""
Classes for data object such as trains or cards in nslib.
"""
import requests
import base64
import uuid
import xmltodict
import datetime

from cachetools import cached, TTLCache

from .stations import STATIONS
from .helpers import getStation
from .nsexceptions import ConnectionError, InvalidCredentials, InvalidCard, TooManyRequests, InvalidResponse, InvalidStation

CARD_CACHE_SEC = 240
TRAIN_CACHE_SEC = 240

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

        if "Minimum request interval exceeded" in rCID.text:
            raise TooManyRequests("Minimum request interval exceeded.") # This endpoint is strictly rate limited, this error will solve itself in a minute or 2

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

        stateObject = {
            "checkedIn": False,
            "trips": []
        }

        try:
            cardData = rCard.json()

            if len(cardData["transactions"]) > 0:
                stateObject["balance"] = cardData["transactions"][0]["remainingPurseValue"]

                for transaction in cardData["transactions"]:
                    trip = {
                        "balance": transaction["remainingPurseValue"],
                        "departure": {}
                    }

                    trip["departure"]["station"] = getStation(transaction["departure"]["station"]["stationCode"])
                    trip["departure"]["time"] = datetime.datetime.strptime(transaction["departure"]["timestamp"], "%d-%m-%Y %H:%M:%S +01:00")

                    if "arrival" in transaction:
                        trip["arrival"] = {
                            "station": getStation(transaction["arrival"]["station"]["stationCode"]),
                            "time": datetime.datetime.strptime(transaction["arrival"]["timestamp"], "%d-%m-%Y %H:%M:%S +01:00")
                        }


                    elif cardData["transactions"].index(transaction) == 0:
                        # If the transaction has no arrival station and is the last transaction, the card is still cheked in
                        stateObject.checkedIn = True

                    stateObject["trips"].append(trip)
        except (KeyError, IndexError, ValueError) as error:
            raise InvalidResponse("Invalid response from NS severs (" + str(error) + "): " + rCard.text) from error

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

class Train(object):
    """Representation of a NS train."""
    def __init__(self, id, provider):
        self.id = id
        self.provider = provider.lower()

        self._type = False

    @property
    @cached(TTLCache(maxsize=1, ttl=TRAIN_CACHE_SEC))
    def _progState(self):

        params = [
            ("ritnummer",  self.id),
            ("companycode", self.provider),
            ("datetime",  datetime.datetime.now().strftime("%Y-%m-%dT%H:%M"))
        ]

        headers = {
            "Accept-Encoding": "gzip",
            "Authorization": "Basic YW5kcm9pZDptdmR6aWc=",
            "User-Agent": "Google-HTTP-Java-Client/1.19.0 (gzip)",
            "Host": "ews-rpx.ns.nl",
            "Connection": "Keep-Alive"
        }

        try:
            rTrain = requests.get("https://ews-rpx.ns.nl/mobile-api-serviceinfo", params=params, headers=headers)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to NS servers.")

        xml = xmltodict.parse(rTrain.text)["ServiceInfoList"]["ServiceInfo"]

        stateObject = {
            "type": xml["TransportModeCode"],
            "stations": []
        }

        self._type = xml["TransportModeCode"]

        for stop in xml["StopList"]["Stop"]:
            outStop = {
                "station": getStation(stop["StopCode"]),
                "stops": False,
                "meta": {}
            }

            if "Arrival" in stop:
                outStop["stops"] = True
                outStop["arrival"] = {
                    "scheduled": datetime.datetime.strptime(stop["Arrival"][:19], "%Y-%m-%dT%H:%M:%S")
                }

                if "ArrivalTimeDelay" in stop:
                    outStop["arrival"]["actual"] = outStop["arrival"]["scheduled"] + datetime.timedelta(minutes=int(stop["ArrivalTimeDelay"][2:-1]))
                else:
                    outStop["arrival"]["actual"] = outStop["arrival"]["scheduled"]

            if "Departure" in stop:
                outStop["stops"] = True
                outStop["departure"] = {
                    "scheduled": datetime.datetime.strptime(stop["Departure"][:19], "%Y-%m-%dT%H:%M:%S")
                }

                if "DepartureTimeDelay" in stop:
                    outStop["departure"]["actual"] = outStop["departure"]["scheduled"] + datetime.timedelta(minutes=int(stop["DepartureTimeDelay"][2:-1]))
                else:
                    outStop["departure"]["actual"] = outStop["departure"]["scheduled"]

            if "prognose" in stop:
                outStop["meta"]["ExpectedPassengers"] = int(stop["prognose"])

            if "punctualiteit" in stop:
                def setMeta(value):
                    if value["@moment"] == "aankomst":
                        outStop["meta"]["ArrivedOnTime"] = float(value["#text"])
                    if value["@moment"] == "vertrek":
                        outStop["meta"]["DepartedOnTime"] = float(value["#text"])

                # If 2 mesures are known it will be a list we need to loop though, otherwise we can just use the dict directly
                if type(stop["punctualiteit"]) == list:
                    for value in stop["punctualiteit"]:
                        setMeta(value)
                else:
                    setMeta(stop["punctualiteit"])


            stateObject["stations"].append(outStop)

        return stateObject

    @property
    def type(self):
        """Update for the type if it has never done before, but otherwise get the locally stored version."""
        if self._type == False:
            return self._progState["type"]
        else:
            return self._type

    @property
    def stations(self):
        """Update for the type if it has never done before, but otherwise get the locally stored version."""
        return self._progState["stations"]
