"""Classifica cookies contra a base de assinaturas de trackers."""
import json
import re
from pathlib import Path

DB_PATH = Path(__file__).parent / "trackers.json"

# Categorias que exigem consentimento prévio
NON_ESSENTIAL = {"analytics", "advertising", "social"}


def load_db(path: Path = DB_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        db = json.load(f)
    for rule in db["cookie_rules"]:
        rule["_re"] = re.compile(rule["pattern"])
    return db


def classify_cookie(cookie: dict, db: dict) -> dict:
    name = cookie["name"]
    domain = cookie["domain"].lstrip(".").lower()

    # 1) Regras por nome do cookie
    for rule in db["cookie_rules"]:
        if rule["_re"].fullmatch(name):
            return {"category": rule["category"], "vendor": rule["vendor"],
                    "matched_by": f"nome: {rule['pattern']}"}

    # 2) Regras por domínio (só pra terceiros, senão auditar facebook.com marcaria tudo)
    if cookie.get("third_party"):
        for rule in db["domain_rules"]:
            d = rule["domain"]
            if domain == d or domain.endswith("." + d):
                return {"category": rule["category"], "vendor": rule["vendor"],
                        "matched_by": f"domínio: {d}"}

    return {"category": "unknown", "vendor": None, "matched_by": None}


def classify_all(cookies: list[dict], db: dict) -> list[dict]:
    results = []
    for c in cookies:
        info = classify_cookie(c, db)
        if info["category"] in NON_ESSENTIAL:
            status = "violation"   # não essencial gravado antes do consentimento
        elif info["category"] == "essential":
            status = "ok"
        else:
            status = "review"      # desconhecido: revisar manualmente
        results.append({**c, **info, "status": status})
    return results


def summarize(classified: list[dict]) -> dict:
    return {
        "total": len(classified),
        "violations": sum(c["status"] == "violation" for c in classified),
        "review": sum(c["status"] == "review" for c in classified),
        "ok": sum(c["status"] == "ok" for c in classified),
    }