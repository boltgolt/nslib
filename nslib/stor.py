import requests
import json

from data.stations import STATIONS

headers = {
    "Accept-Encoding": "gzip",
    "Authorization": "Basic YW5kcm9pZDptdmR6aWc=",
    "Connection": "Keep-Alive",
    "User-Agent": "Google-HTTP-Java-Client/1.19.0 (gzip)"
}

rNow = requests.get("https://ews-rpx.ns.nl/private-ns-api/json/v1/verstoringen?actual=true", headers=headers)
rPlanned = requests.get("https://ews-rpx.ns.nl/private-ns-api/json/v1/verstoringen?type=werkzaamheid", headers=headers)

disruptionArray = rPlanned.json()
disruptionArray = disruptionArray["payload"]
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
            outStop = STATIONS[stop.upper()]

            if "begintijd" in track:
                outStop["starts"] = track["begintijd"]
            if "eindtijd" in track:
                outStop["ends"] = track["eindtijd"]

            outDis["stations"].append(outStop)

    output.append(outDis)

print(json.dumps(output))
