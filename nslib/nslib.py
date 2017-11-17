import requests
import xmltodict
import json
import logging

from datetime import datetime, timedelta
from cachetools import cached, TTLCache

from .classes import Account, Card, Train
from .helpers import getStation, fetchStations
from .nsexceptions import MalfomedRoute, InvalidStation

from .stations import STATIONS

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

DISRUPTIONS_CACHE_SEC = 60

try:
    from .stations import RETRIEVED
    sinceRetrieve = datetime.now() - datetime.strptime(RETRIEVED, "%Y-%m-%d %H:%M:%S")

    if timedelta(days=60) < sinceRetrieve:
        _LOGGER.info("Refreshing stale {}-days-old station data.".format(sinceRetrieve.days))
        fetchStations()
    else:
        _LOGGER.debug("Using station cache, as it is only {} days old.".format(sinceRetrieve.days))
except ImportError:
    _LOGGER.info("Fetching station data for the first time.")
    fetchStations()

def getDisruptions():
    """Current and planned disruptions on the rail network."""
    headers = {
        "Accept-Encoding": "gzip",
        "Authorization": "Basic YW5kcm9pZDptdmR6aWc=",
        "Connection": "Keep-Alive",
        "User-Agent": "Google-HTTP-Java-Client/1.19.0 (gzip)"
    }

    rNow = requests.get("https://ews-rpx.ns.nl/private-ns-api/json/v1/verstoringen?actual=true", headers=headers)
    rPlanned = requests.get("https://ews-rpx.ns.nl/private-ns-api/json/v1/verstoringen?type=werkzaamheid", headers=headers)

    disruptionArray = rPlanned.json()["payload"]
    foundDisruptions = []
    output = []

    for dis in disruptionArray:
        foundDisruptions.append(dis["id"])

    currentDisruptions = rNow.json()["payload"]

    for dis in currentDisruptions:
        if dis["id"] not in foundDisruptions:
            disruptionArray.append(dis)

    for dis in disruptionArray:
        outDis = {
            "id": dis["id"],
            "title": dis["header"],
            "cause": dis["oorzaak"],
            "effect": dis["gevolg"],
            "stations": []
        }

        for track in dis["trajecten"]:
            for stop in track["stations"]:
                outStop = {
                    station: getStation(stop)
                }

                if "begintijd" in track:
                    outStop["starts"] = track["begintijd"]
                if "eindtijd" in track:
                    outStop["ends"] = track["eindtijd"]

                outDis["stations"].append(outStop)

        output.append(outDis)

    return output

def getRoute(route, time=datetime.now()):
    """Get route options between 2 to 3 points."""
    if len(route) < 2:
        raise MalfomedRoute("Route array should contain at least 2 stations.")
    if len(route) > 3:
        raise MalfomedRoute("Route array should not contain more than 3 stations.")

    for stationCode in route:
        if stationCode not in STATIONS:
            raise InvalidStation("\"%s\" is not a valid station code." % stationCode)

    params = [
        ("callerid",  "RPX:reisadvies"),
        ("departure",  "true"),
        ("hslAllowed",  "true"),
        ("yearCard",  "false"),
        ("minimalChangeTime",  "0"),
        ("travelAdviceType",  "OPTIMAL"),
        ("dateTime",  time.strftime("%Y-%m-%dT%H:%M")),
        ("previousAdvices",  "1"),
        ("nextAdvices",  "6"),
        ("passing",  "true"),
        ("product",  "GEEN")
    ]

    params.append(("fromStation", route[0]))

    if len(route) == 2:
        params.append(("toStation", route[1]))
    else:
        params.append(("viaStation", route[1]))
        params.append(("toStation", route[2]))

    rRoute = requests.get("https://ews-rpx.ns.nl/mobile-api-planner", params = params, headers = {
        "Accept-Encoding": "gzip",
        # The default username and password (android, mvdzig) works for any non-auth endpoint
        "Authorization": "Basic YW5kcm9pZDptdmR6aWc=",
        "Connection": "Keep-Alive",
        "User-Agent": "ReisplannerXtra/5.0.14 "
    })

    routes = xmltodict.parse(rRoute.text)
    routes = routes["ReisMogelijkheden"]["ReisMogelijkheid"]
    output = []

    for route in routes:
        outRoute = {
            "transfers": route["AantalOverstappen"],
            "asSchuduled": True if route["Status"] == "AS_SCHEDULED" else False,
            "depature": {
                "scheduled": route["GeplandeVertrekTijd"],
                "actual": route["ActueleVertrekTijd"]
            },
            "arrival": {
                "scheduled": route["GeplandeAankomstTijd"],
                "actual": route["ActueleAankomstTijd"]
            },
            "legs": []
        }

        for leg in route["ReisDeel"]:
            outLeg = {
                "provider": leg["Vervoerder"],
                "id": leg["RitNummer"],
                "asSchuduled": True if leg["Status"] == "AS_SCHEDULED" else False,
                "stops": []
            }

            if "Richting" in leg:
                outLeg["finalDestination"] = leg["Richting"]

            if "UitstapZijde" in leg:
                outLeg["exitSide"] = "right" if leg["UitstapZijde"] == "Rechts" else "left"

            for stop in leg["ReisStop"]:
                outStop = {
                    station: getStation(stop["Code"])
                }

                outStop["nonstop"] = False if stop["@type"] == "STOP" else True


                if "Tijd" in stop:
                    outStop["time"] = stop["Tijd"]

                if "Spoor" in stop:
                    outStop["track"] = stop["Spoor"]["#text"]

                outLeg["stops"].append(outStop)

            outRoute["legs"].append(outLeg)

        output.append(outRoute)

    return output

def getDepartures(station):
    """Get departing trains from a station."""
    if station not in STATIONS:
        raise InvalidStation("\"%s\" is not a valid station code." % station)

    response = requests.get("https://ews-rpx.ns.nl/mobile-api-avt", params = [
        ("station", station)
    ], headers = {
        "Accept-Encoding": "gzip",
        "Authorization": "Basic YW5kcm9pZDptdmR6aWc=",
        "Connection": "Keep-Alive",
        "User-Agent": "ReisplannerXtra/5.0.14 "
    })

    departures = xmltodict.parse(response.text)["ActueleVertrekTijden"]["VertrekkendeTrein"]
    output = []

    for departure in departures:
        output.append({
            "finalDestination": departure["EindBestemming"],
            "id": departure["RitNummer"],
            "type": departure["TreinSoort"],
            "track": departure["VertrekSpoor"]["#text"],
            "time": departure["VertrekTijd"],
            "provider": departure["Vervoerder"]
        })

    return output
