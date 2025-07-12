import requests
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from urllib.parse import urlencode, quote

base_url = "https://www.churchofjesuschrist.org/media/music/api"
params = {
    "type": "songsFilteredList",
    "lang": "ita",
    "identifier": quote(json.dumps({
        "lang": "ita",
        "limit": 500,
        "offset": 0,
        "orderByKey": ["bookSongPosition"],
        "bookQueryList": ["hymns"]
    })),
    "batchSize": 20
}

API_URL = f"{base_url}?type={params['type']}&lang={params['lang']}&identifier={params['identifier']}&batchSize={params['batchSize']}"

app = FastAPI()

def get_hymns_list():
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    hymns = []
    for item in data.get('data', []):
        hymn = {}
        hymn['number'] = item.get('songNumber')
        hymn['name'] = item.get('title')
        hymn['tags'] = ', '.join(item.get('tags', []))
        hymn['category'] = item.get('bookSectionTitle', '')
        hymn['url'] = item.get('assets', [{}])[0].get('mediaObject', {}).get('distributionUrl', '') if item.get('assets') else ''
        hymns.append(hymn)
    return hymns

def get_hymns_full_data():
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    return data.get('data', [])

# Endpoint to get a brief list of hymns in CSV
@app.get("/hymns")
def hymns_list():
    hymns = get_hymns_list()
    return JSONResponse(content=hymns)

# Endpoint to get full hymn data in JSON
@app.get("/hymns/full")
def hymns_full():
    full_data = get_hymns_full_data()
    return JSONResponse(content=full_data)
