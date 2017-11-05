import requests
import xmltodict
import json

response = requests.get("https://ews-rpx.ns.nl/mobile-api-avt", params = [
    ("station", "MG")
], headers = {
    "Accept-Encoding": "gzip",
    "Authorization": "Basic YW5kcm9pZDptdmR6aWc=",
    "Connection": "Keep-Alive",
    "User-Agent": "ReisplannerXtra/5.0.14 "
})

departures = xmltodict.parse(response.text)
departures = departures["ActueleVertrekTijden"]["VertrekkendeTrein"]

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

print(json.dumps(output))
