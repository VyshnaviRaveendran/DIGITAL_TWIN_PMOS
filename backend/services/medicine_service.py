# backend/services/medicine_service.py
import os
import re
import pandas as pd
from typing import List, Dict, Any

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pmos_medicines.csv")

def load_medicine_dataset() -> pd.DataFrame:
    if os.path.exists(DATASET_PATH):
        try:
            return pd.read_csv(DATASET_PATH).fillna("")
        except Exception as e:
            print(f"Error loading pmos_medicines.csv: {e}")
    return pd.DataFrame()

MED_DF = load_medicine_dataset()

def build_search_corpus(df: pd.DataFrame) -> List[Dict[str, Any]]:
    corpus = []
    if df.empty:
        return corpus
    for _, row in df.iterrows():
        gen_name = str(row.get("generic_name", "")).strip()
        if not gen_name:
            continue
        corpus.append({
            "term": gen_name.lower(),
            "display_name": gen_name,
            "data": row.to_dict(),
            "is_brand": False
        })
        brands = str(row.get("brand_names", ""))
        if brands:
            for brand in brands.split(";"):
                clean_brand = brand.strip()
                if clean_brand:
                    corpus.append({
                        "term": clean_brand.lower(),
                        "display_name": f"{clean_brand} ({gen_name})",
                        "data": row.to_dict(),
                        "is_brand": True
                    })
    return corpus

SEARCH_CORPUS = build_search_corpus(MED_DF)

def get_medication_suggestions(query: str = "") -> List[Dict[str, Any]]:
    q = query.lower().strip()
    if not q or len(q) < 2:
        return []
    results = []
    seen_generics = set()
    for item in SEARCH_CORPUS:
        if q in item["term"]:
            generic = item["data"].get("generic_name", "")
            if generic not in seen_generics:
                seen_generics.add(generic)
                results.append({
                    "name": item["display_name"],
                    "default_dosage": item["data"].get("default_dosage", "Once daily"),
                    "purpose": item["data"].get("clinical_purpose", "PMOS Support"),
                    "category": item["data"].get("category", "Supplement"),
                    "icon": item["data"].get("icon", "💊"),
                    "score": 100
                })
    return results[:6]

def scan_prescription_text(filename: str = "", extracted_text: str = "") -> Dict[str, Any]:
    combined_text = f"{filename} {extracted_text}".lower()
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', combined_text)
    best_match = None

    for item in SEARCH_CORPUS:
        term = item["term"]
        if len(term) < 3:
            continue
        if term in clean_text:
            best_match = item
            break

    if best_match:
        data = best_match["data"]
        dosage = data.get("default_dosage", "Once daily")
        if any(w in clean_text for w in ["0 0 1", "0-0-1", "night", "9 pm", "bedtime"]):
            if "night" not in dosage.lower():
                dosage = f"{dosage.split('|')[0].strip()} | Night (After Meal)"
        elif any(w in clean_text for w in ["1 0 0", "1-0-0", "morning"]):
            if "morning" not in dosage.lower():
                dosage = f"{dosage.split('|')[0].strip()} | Morning (After Meal)"

        return {
            "name": f"{best_match['display_name']}",
            "dosage": dosage,
            "purpose": data.get("clinical_purpose", "Prescribed Protocol"),
            "category": data.get("category", "Therapeutic"),
            "icon": data.get("icon", "💊"),
            "confidence": 0.95,
            "not_found": False
        }

    return {
        "name": "",
        "dosage": "",
        "purpose": "",
        "icon": "💊",
        "confidence": 0.0,
        "not_found": True
    }
