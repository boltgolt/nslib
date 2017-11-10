def getStation(code):
    from .stations import STATIONS

    code = code.upper()

    if code not in STATIONS:
        raise InvalidStation("\"%s\" is not a valid station code." % code)

    station = STATIONS[code]
    station["code"] = code

    return station
