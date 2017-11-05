import requests
import xmltodict
import json

from data.stations import STATIONS

response = requests.get("https://ews-rpx.ns.nl/mobile-api-planner", params = [
    ("fromStation", "LC"),
    ("viaStation",  "MG"),
    ("toStation",  "RTB"),
    ("callerid",  "RPX:reisadvies"),
    ("departure",  "true"),
    ("hslAllowed",  "true"),
    ("yearCard",  "false"),
    ("minimalChangeTime",  "0"),
    ("travelAdviceType",  "OPTIMAL"),
    ("dateTime",  "2017-11-05T12:33"),
    ("previousAdvices",  "1"),
    ("nextAdvices",  "6"),
    ("passing",  "true"),
    ("product",  "GEEN")
], headers = {
    "Accept-Encoding": "gzip",
    "Authorization": "Basic YW5kcm9pZDptdmR6aWc="
    "Connection": "Keep-Alive",
    "User-Agent": "ReisplannerXtra/5.0.14 "
})

trips = xmltodict.parse(response.text)
trips = trips["ReisMogelijkheden"]["ReisMogelijkheid"]
output = []

for trip in trips:
    outTrip = {
        "transfers": trip["AantalOverstappen"],
        "asSchuduled": True if trip["Status"] == "AS_SCHEDULED" else False,
        "depature": {
            "scheduled": trip["GeplandeVertrekTijd"],
            "actual": trip["ActueleVertrekTijd"]
        },
        "arrival": {
            "scheduled": trip["GeplandeAankomstTijd"],
            "actual": trip["ActueleAankomstTijd"]
        },
        "legs": []
    }

    for leg in trip["ReisDeel"]:
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
            outStop = STATIONS[stop["Code"]]

            outStop["nonstop"] = False if stop["@type"] == "STOP" else True


            if "Tijd" in stop:
                outStop["time"] = stop["Tijd"]

            if "Spoor" in stop:
                outStop["track"] = stop["Spoor"]["#text"]

            outLeg["stops"].append(outStop)

        outTrip["legs"].append(outLeg)

    output.append(outTrip)

print(json.dumps(output))
