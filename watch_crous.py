#!/usr/bin/env python3
"""
Surveille la page de recherche de logement CROUS et envoie une notification
push sur ton téléphone (via ntfy.sh) à CHAQUE vérification : soit "nouvelle
offre trouvée", soit "rien de nouveau" (heartbeat pour savoir que ça tourne).
"""

import json
import os
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

STATE_FILE = Path(__file__).parent / "seen.json"

DEFAULT_SEARCH_URL = "https://trouverunlogement.lescrous.fr/tools/42/search"
CITY_FILTER = os.environ.get("CITY_FILTER", "MONTPELLIER")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "crous-mtp-alerte-CHANGE-MOI-123")
TEST_NOTIFICATION = os.environ.get("TEST_NOTIFICATION", "false").lower() == "true"


def send_test_notification():
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data="Ceci est une notification de test envoyée depuis GitHub Actions. Si tu la reçois, tout le circuit fonctionne !".encode("utf-8"),
            headers={
                "Title": "✅ Test crous-watcher".encode("utf-8"),
                "Priority": "default",
                "Tags": "white_check_mark",
            },
            timeout=15,
        )
        print("Notification de TEST envoyée.")
    except Exception as e:
        print(f"Erreur d'envoi de la notif de test : {e}", file=sys.stderr)


def fetch_listings(search_url: str) -> list[dict]:
    listings = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(search_url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("a[href*='/accommodations/']")
        for card in cards:
            href = card.get_attribute("href")
            text = card.inner_text().strip()
            if not href or not text:
                continue
            if CITY_FILTER and CITY_FILTER.upper() not in text.upper():
                continue
            full_url = href if href.startswith("http") else f"https://trouverunlogement.lescrous.fr{href}"
            listings.append({
                "id": full_url,
                "title": text.split("\n")[0][:120],
                "summary": " | ".join(text.split("\n")[:4]),
                "url": full_url,
            })
        browser.close()
    unique = {l["id"]: l for l in listings}
    return list(unique.values())


def load_seen() -> set:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_seen(ids: set):
    STATE_FILE.write_text(json.dumps(sorted(ids), ensure_ascii=False, indent=2))


def notify(new_listings: list[dict]):
    for listing in new_listings:
        title = "🏠
