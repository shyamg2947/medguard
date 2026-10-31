"""
Rules Loader & Validator.
Reads and validates rules from rules/seed_rules.yaml using Pydantic schema.
"""
import os
from typing import List, Optional
import yaml
from backend.app.rules.schema import RuleDefinition


def load_rules(file_path: Optional[str] = None) -> List[RuleDefinition]:
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "../../../rules/seed_rules.yaml")

    rules: List[RuleDefinition] = []
    if not os.path.exists(file_path):
        return rules

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        for r_dict in data.get("rules", []):
            try:
                # Handle target aliases
                if "a" in r_dict and isinstance(r_dict["a"], dict) and "class" in r_dict["a"]:
                    r_dict["a"]["class_name"] = r_dict["a"].pop("class")
                if "b" in r_dict and isinstance(r_dict["b"], dict) and "class" in r_dict["b"]:
                    r_dict["b"]["class_name"] = r_dict["b"].pop("class")
                if "combo" in r_dict and isinstance(r_dict["combo"], list):
                    for item in r_dict["combo"]:
                        if isinstance(item, dict) and "class" in item:
                            item["class_name"] = item.pop("class")

                rule = RuleDefinition.model_validate(r_dict)
                rules.append(rule)
            except Exception as ex:
                print(f"Warning: Failed to validate rule {r_dict.get('id')}: {ex}")

    return rules
