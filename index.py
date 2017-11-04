import requests
import base64
import uuid



bearer = base64.b64encode(USER + ":" + PASS)

headers = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Authorization": "Basic " + bearer,
    "User-Agent": "Google-HTTP-Java-Client/1.19.0 (gzip)",
    "connection": "Close",
    "Host": "ews-rpx.ns.nl",
    "content-length": "0"
}

r = requests.get("https://ews-rpx.ns.nl/private-reistransacties-api/service/cards", headers=headers)

print r.json()

headers = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Authorization": "Basic " + bearer,
    "User-Agent": "Google-HTTP-Java-Client/1.19.0 (gzip)",
    "connection": "Close",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "ews-rpx.ns.nl",
    "content-length": "0"
}

r = requests.post("https://ews-rpx.ns.nl/private-reistransacties-api/service/selectcard/" + str(r.json()["cards"][0]["ovcpNumber"]), headers=headers)

print r.text
print str(uuid.uuid4())

headers = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
    "X-Request-ID": str(uuid.uuid4()),
    "Authorization": "Basic " + bearer,
    "User-Agent": "rpx_android/5.0.14:519",
    "connection": "Keep-Alive",
    "Host": "ews-rpx.ns.nl",
    "content-length": "0"
}

r = requests.get("https://ews-rpx.ns.nl/private-reistransacties-api/service/transactions/" + r.json()["cid"], headers=headers)

print r.text
