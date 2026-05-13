import json
from pathlib import Path

BASE_DIR = Path(r"C:\TaxCaseManager")
POLICY_FILE = BASE_DIR / "legal_knowledge" / "rules" / "judgment_phrase_policy.json"

def load_judgment_policy():
    if not POLICY_FILE.exists():
        return {}
    try:
        with open(POLICY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def get_judgment_level(code):
    policy = load_judgment_policy()
    levels = policy.get("judgment_levels", [])
    for level in levels:
        if level.get("code") == code:
            return level
    return None

def apply_judgment_phrase(level_code, additional_context=""):
    level = get_judgment_level(level_code)
    if not level:
        return ""
    
    phrase = level.get("phrase", "")
    name = level.get("name", "")
    
    result = f"[{name}] {phrase}"
    if additional_context:
        result += f"\n- {additional_context}"
    return result
