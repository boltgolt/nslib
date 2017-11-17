def fetchStations():
    import datetime
    import json
    import requests
    import os

    from .nsexceptions import InvalidResponse

    countryCodes = {
        "A": "AT",
        "B": "BE",
        "D": "DE",
        "F": "FR",
        "H": "HU",
        "I": "IT",
    }

    headers = {
        "Authorization": "Basic YW5kcm9pZDptdmR6aWc=",
        "Host": "reisinfo.ns-mlab.nl",
        "Connection": "Keep-Alive",
        "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
    }

    rStations = requests.get("https://reisinfo.ns-mlab.nl/api/v2/stations", headers=headers)

    if rStations.status_code != 200:
        raise InvalidResponse("Request resulted in {} status code".format(rStations.status_code))

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

    f = open(os.path.dirname(os.path.realpath(__file__)) + "/stations.py", "w")
    f.write("#\tTHIS FILE IS DYNAMICALLY GENERATED, ANY MANUAL CHANGES MADE WILL BE LOST\n")
    f.write("#\tThe next regeneration of this file will be sometime after {}\n\n".format((datetime.datetime.now() + datetime.timedelta(60)).strftime("%Y-%m-%d at %H:%M:%S")))

    f.write("RETRIEVED = '{}'\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    f.write("STATIONS = " + json.dumps(output))
    f.close()

    _LOGGER.info("Successfully indexed {}KB of station data.".format(round(len(rStations.content) / 1024,1)))

def getStation(code):
    from .stations import STATIONS

    code = code.upper()

    if code not in STATIONS:
        raise InvalidStation("\"%s\" is not a valid station code." % code)

    station = STATIONS[code]
    station["code"] = code

    return station
