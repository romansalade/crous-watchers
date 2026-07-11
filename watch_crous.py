#!/usr/bin/env python3
"""
Surveille la page de recherche de logement CROUS (Montpellier) et envoie
une notification push sur ton téléphone (via ntfy.sh) dès qu'une NOUVELLE
offre apparaît.
"""

import json
import os
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

STATE_FILE = Path(__file__).parent / "seen.json"

DEFAULT_SEARCH_URL = "https://trouverunlogement.lescrous.fr/tools/42/search"
CITY_FILTER = "MONTPELLIER"
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "crous-mtp-alerte-CHANGE-MOI-123")


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
            if CITY_FILTER.upper() not in text.upper():
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
        title = "🏠 Nouveau logement CROUS Montpellier !"
        message = f"{listing['summary']}\n\n{listing['url']}"
        try:
            requests.post(
                f"https://ntfy.sh/{NTFY_TOPIC}",
                data=message.encode("utf-8"),
                headers={
                    "Title": title.encode("utf-8"),
                    "Priority": "high",
                    "Tags": "house,bell",
                    "Click": listing["url"],
                },
                timeout=15,
            )
            print(f"Notification envoyée pour : {listing['title']}")
        except Exception as e:
            print(f"Erreur d'envoi ntfy pour {listing['title']}: {e}", file=sys.stderr)


def main():
    search_url = os.environ.get("CROUS_URL") or DEFAULT_SEARCH_URL
    print(f"Vérification de : {search_url}")

    listings = fetch_listings(search_url)
    print(f"{len(listings)} logement(s) trouvé(s) à Montpellier.")

    seen = load_seen()
    new_ids = {l["id"] for l in listings} - seen

    if new_ids:
        new_listings = [l for l in listings if l["id"] in new_ids]
        print(f"{len(new_listings)} NOUVELLE(S) offre(s) !")
        notify(new_listings)
    else:
        print("Rien de nouveau.")

    save_seen({l["id"] for l in listings} | seen)


if __name__ == "__main__":
    main()
