import json
import requests

countryCodes = {
    "A": "AT",
    "B": "BE",
    "D": "DE",
    "F": "FR",
    "H": "HU",
    "I": "IT",
}

print "Fetching station info..."

headers = {
    "Authorization": "Basic YW5kcm9pZDptdmR6aWc=",
    "Host": "reisinfo.ns-mlab.nl",
    "Connection": "Keep-Alive",
    "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
}

rStations = requests.get("https://reisinfo.ns-mlab.nl/api/v2/stations", headers=headers)

print "Got %s response, formatting data.." % rStations.status_code

data = rStations.json()
output = {}

for station in data["payload"]:
    output[station["code"]] = {
        "country": station["land"] if len(station["land"]) == 2 else countryCodes[station["land"]],
        "UICCode": station["UICCode"],
        "location": {
            "lat": station["lat"],
            "lng": station["lng"]
        },
        "names": {
            "full": station["namen"]["lang"],
            "short": station["namen"]["middel"],
            "tiny": station["namen"]["kort"]
        }
    }

print "Writing data to file..."

f = open("stations.py", "w")
f.write("STATIONS = " + json.dumps(output))
f.close()

print "Done."
