import json

countryCodes = {
    "A": "AT",
    "B": "BE",
    "D": "DE",
    "F": "FR",
    "H": "HU",
    "I": "IT",
}

with open("stations.json") as stations_file:
    data = json.load(stations_file)

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

f = open("stations.py", "w")
f.write("STATIONS = " + json.dumps(output))
f.close()
