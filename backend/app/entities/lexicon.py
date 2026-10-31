"""
Medication Lexicon & Knowledge Directory.
Loads brand-to-generic mappings, herbal products, and transliteration tables.
"""
import csv
import os
from typing import Any, Dict, List, Optional, Set
import yaml

# Indic transliterations for common Indian medicine names
INDIC_TRANSLITERATIONS: Dict[str, str] = {
    # Hindi Devanagari to Latin
    "डोलो": "dolo",
    "क्रोसिन": "crocin",
    "कॉम्बीफ्लाम": "combiflam",
    "ब्रुफेन": "brufen",
    "वोवेरान": "voveran",
    "इकोस्प्रिन": "ecosprin",
    "टेल्मा": "telma",
    "एम्लॉन्ग": "amlong",
    "कार्डासि": "cardace",
    "बेटालाक": "betaloc",
    "लासिक": "lasix",
    "ग्लुकोमेट": "glycomet",
    "ग्लिकोमेट": "glycomet",
    "अटोरवा": "atorva",
    "पैन": "pan",
    "ओमेज़": "omez",
    "एल्प्राक्स": "alprax",
    "अश्वगंधा": "ashwagandha",
    "हल्दी": "turmeric",
    "लहसुन": "garlic supplement",
    "त्रिफला": "triphala",
    "गिलोय": "giloy",
    "ब्राह्मी": "brahmi",
    "पेरासिटामोल": "paracetamol",
    "आइबुप्रोफेन": "ibuprofen",
    "डाइक्लोफेनाक": "diclofenac",
    "एस्पिरिन": "aspirin",
    "वारफारिन": "warfarin",
    "मेटफॉर्मिन": "metformin",
    "एम्लोडिपिन": "amlodipine",
    "टेल्मिसार्टन": "telmisartan",
}


class Lexicon:
    _instance = None

    def __init__(self):
        self.brands: Dict[str, Dict[str, Any]] = {}
        self.generics: Set[str] = set()
        self.classes: Dict[str, List[str]] = {}
        self.ingredient_to_classes: Dict[str, List[str]] = {}
        self.class_domains: Dict[str, str] = {}
        self.herbal_entries: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    @classmethod
    def get_instance(cls) -> "Lexicon":
        if cls._instance is None:
            cls._instance = Lexicon()
        return cls._instance

    def _load_all(self):
        # 1. Load Lexicon Seed CSV
        csv_path = os.path.join(os.path.dirname(__file__), "../../../data/lexicon_seed.csv")
        if os.path.exists(csv_path):
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    brand_name = row["brand"].strip()
                    ingredients_raw = row["ingredients"].strip()
                    form = row.get("form", "tablet").strip()
                    category = row.get("category", "prescription").strip()
                    source = row.get("source", "Standard Reference").strip()

                    # Parse ingredients: "ibuprofen:400mg|paracetamol:325mg"
                    ing_list = []
                    for item in ingredients_raw.split("|"):
                        if ":" in item:
                            name, strength = item.split(":", 1)
                        else:
                            name, strength = item, ""
                        name = name.strip().lower()
                        ing_list.append({"ingredient": name, "strength": strength.strip()})
                        self.generics.add(name)

                    self.brands[brand_name.lower()] = {
                        "brand": brand_name,
                        "ingredients": ing_list,
                        "form": form,
                        "category": category,
                        "source": source,
                    }

        # 2. Load Classes YAML
        classes_path = os.path.join(os.path.dirname(__file__), "../../../rules/classes.yaml")
        if os.path.exists(classes_path):
            with open(classes_path, mode="r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                raw_classes = data.get("classes", {})
                for cls_name, cls_info in raw_classes.items():
                    ings = cls_info.get("ingredients", [])
                    domain = cls_info.get("domain", "General")
                    self.classes[cls_name] = [i.lower() for i in ings]
                    self.class_domains[cls_name] = domain
                    for ing in ings:
                        ing_lower = ing.lower()
                        self.generics.add(ing_lower)
                        if ing_lower not in self.ingredient_to_classes:
                            self.ingredient_to_classes[ing_lower] = []
                        if cls_name not in self.ingredient_to_classes[ing_lower]:
                            self.ingredient_to_classes[ing_lower].append(cls_name)

        # 3. Load Herbal YAML
        herbal_path = os.path.join(os.path.dirname(__file__), "../../../rules/herbal.yaml")
        if os.path.exists(herbal_path):
            with open(herbal_path, mode="r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                for prod in data.get("herbal_products", []):
                    cname = prod["canonical_name"].lower()
                    self.herbal_entries[cname] = prod
                    self.generics.add(cname)
                    for alias in prod.get("aliases", []):
                        self.brands[alias.lower()] = {
                            "brand": alias.title(),
                            "ingredients": [{"ingredient": cname, "strength": ""}],
                            "form": "herbal",
                            "category": prod.get("category", "ayush"),
                            "source": "Ayurvedic Pharmacopoeia",
                        }

    def get_classes_for_ingredient(self, ingredient: str) -> List[str]:
        return self.ingredient_to_classes.get(ingredient.lower(), [])

    def get_brand_entry(self, brand: str) -> Optional[Dict[str, Any]]:
        return self.brands.get(brand.lower())


def get_lexicon() -> Lexicon:
    return Lexicon.get_instance()

