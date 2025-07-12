from fastapi import FastAPI, Query
from typing import List, Optional, Literal
from enum import Enum
import json
import random
import os


# --- Models and Enums ---
class FestivityType(str, Enum):
    natale = "natale"
    pasqua = "pasqua"

class Hymn:
    def __init__(self, data):
        self.number = data.get("songNumber")
        self.name = data.get("title")
        self.tags = [t.lower() for t in data.get("tags", [])]
        self.category = data.get("bookSectionTitle", "")
        self.url = data.get("assets", [{}])[0].get("mediaObject", {}).get("distributionUrl", "") if data.get("assets") else ""
        self.raw = data

    def is_sacramento(self):
        return self.category.strip().lower() == "sacramento"

    def is_special(self):
        return self.category.strip().lower() == "occasioni speciali"

    def has_festive_tag(self, tipo: FestivityType = None):
        if tipo:
            return tipo.value in self.tags
        return "natale" in self.tags or "pasqua" in self.tags

    def brief(self):
        return {
            "number": self.number,
            "name": self.name,
            "tags": self.tags,
            "category": self.category,
            "url": self.url
        }

class HymnRepository:
    def __init__(self, hymns_data):
        self.hymns = [Hymn(h) for h in hymns_data]

    def sacramento_hymns(self):
        return [h for h in self.hymns if h.is_sacramento()]

    def other_hymns(self, include_special=False, festivity: FestivityType = None):
        if festivity:
            return [h for h in self.hymns if not h.is_sacramento() and (h.is_special() or h.has_festive_tag(festivity))]
        elif include_special:
            return [h for h in self.hymns if not h.is_sacramento()]
        else:
            return [h for h in self.hymns if not h.is_sacramento() and not h.is_special() and not h.has_festive_tag()]

class HymnService:
    def __init__(self, repo: HymnRepository):
        self.repo = repo

    def generate(self, prima_domenica: bool = False, domenica_festiva: bool = False, tipo_festivita: FestivityType = None):
        n = 3 if prima_domenica else 4
        sacramento_hymns = self.repo.sacramento_hymns()
        if domenica_festiva:
            if not tipo_festivita:
                return []
            other_hymns = self.repo.other_hymns(festivity=tipo_festivita)
        else:
            other_hymns = self.repo.other_hymns()
        if not sacramento_hymns or len(other_hymns) < n-1:
            return []
        selected = random.sample(other_hymns, n-1)
        sacramento = random.choice(sacramento_hymns)
        selected.insert(1, sacramento)
        return [h.brief() for h in selected]

app = FastAPI()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
HYMNS_JSON_PATH = os.path.join(DATA_DIR, "italian_hymns_full.json")
with open(HYMNS_JSON_PATH, encoding="utf-8") as f:
    hymns_data = json.load(f)
repo = HymnRepository(hymns_data)
service = HymnService(repo)


@app.get("/get_hymns")
def api_get_hymns(
    prima_domenica: bool = Query(False, description="Se true, restituisce 3 inni per la prima domenica (digiuno e testimonianze), altrimenti 4."),
    domenica_festiva: bool = Query(False, description="Se true, include anche inni da 'Occasioni speciali' o con tag 'natale' o 'pasqua'."),
    tipo_festivita: Optional[FestivityType] = Query(None, description="Obbligatorio se domenica_festiva è true. Scegli tra 'natale' o 'pasqua'.")
):
    """Genera una lista di inni secondo le regole. Il secondo inno è sempre dal 'Sacramento'. Se domenica_festiva è true, tipo_festivita è obbligatorio."""
    result = service.generate(prima_domenica, domenica_festiva, tipo_festivita)
    if not result:
        return {"error": "Not enough hymns to generate list or missing 'tipo_festivita' for festive Sunday."}
    return {
        "prima_domenica": prima_domenica,
        "domenica_festiva": domenica_festiva,
        "tipo_festivita": tipo_festivita,
        "hymns": result
    }

@app.get("/get_hymn")
def api_get_hymn(
    category: Optional[str] = Query(None, description="Categoria dell'inno (es. 'Sacramento', 'Occasioni speciali', ecc.)"),
    tag: Optional[str] = Query(None, description="Tag dell'inno (es. 'natale', 'pasqua', ecc.)"),
    number: Optional[int] = Query(None, description="Numero dell'inno (songNumber)")
):
    """Restituisce un solo inno filtrato per numero, categoria o tag (tutti opzionali, AND logico). Se più di uno corrisponde, ne restituisce uno a caso."""
    filtered = service.repo.hymns
    if number is not None:
        filtered = [h for h in filtered if h.number == number]
    if category is not None:
        filtered = [h for h in filtered if h.category.strip().lower() == category.strip().lower()]
    if tag is not None:
        filtered = [h for h in filtered if tag.strip().lower() in h.tags]
    if not filtered:
        return {"error": "No hymn found with the given criteria."}
    hymn = random.choice(filtered)
    return hymn.brief()