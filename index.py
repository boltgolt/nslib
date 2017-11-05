import requests
import base64
import uuid
import datetime

from nsexceptions import (ConnectionError, InvalidCredentials, InvalidCard, TooManyRequests)

defaultHeaders = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip,deflate,sdch",
    "User-Agent": "Google-HTTP-Java-Client/1.19.0 (gzip)",
    "connection": "Close",
    "Host": "ews-rpx.ns.nl",
    "content-length": "0"
}

class NsAccount(object):
    def __init__(self, username, password):
        self.user = username
        self.password = username
        self.cards = []

        self._CIDs = {}
        self._bearer = base64.b64encode(username + ":" + password)

        self._login()

        defaultHeaders["Authorization"] = "Basic " + self._bearer

    def _login(self):
        headers = defaultHeaders
        headers["Authorization"] = "Basic " + self._bearer

        try:
            rLogin = requests.get("https://ews-rpx.ns.nl/private-reistransacties-api/service/cards", headers=headers)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to NS servers.")

        if "401 Unauthorized" in rLogin.text:
            raise InvalidCredentials("The username or password are invalid.")

        for card in rLogin.json()["cards"]:
            self.cards.append(card["ovcpNumber"])

    def readCard(self, card):
        from data.stations import STATIONS

        if card not in self.cards:
            raise InvalidCard("\"%s\" is not a valid card number." % (card))

        if card not in self._CIDs:
            headers = defaultHeaders
            headers["Content-Type"] = "application/x-www-form-urlencoded"

            try:
                rCID = requests.post("https://ews-rpx.ns.nl/private-reistransacties-api/service/selectcard/" + str(card), headers=headers)
            except requests.exceptions.ConnectionError:
                raise ConnectionError("Could not connect to NS servers.")

            if "Minimum request interval exceeded" in rCID.text:
                raise TooManyRequests("Minimum request interval exceeded.")

            self._CIDs[card] = rCID.json()["cid"]

        headers = defaultHeaders
        headers["Accept-Encoding"] = "gzip"
        headers["X-Request-ID"] = str(uuid.uuid4())
        headers["User-Agent"] = "rpx_android/5.0.14:519"
        headers["connection"] = "Keep-Alive"

        try:
            rCard = requests.get("https://ews-rpx.ns.nl/private-reistransacties-api/service/transactions/" + self._CIDs[card], headers=headers)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to NS servers.")

        cardData = rCard.json()

        returnObject = {
            "card": card,
            "checkedin": False,
            "trips": []
        }

        if len(cardData["transactions"]) > 0:
            returnObject["balance"] = cardData["transactions"][0]["remainingPurseValue"]

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

                returnObject["trips"].append(trip)

        return returnObject
