#!/usr/bin/env python3
"""
Surveille la page de recherche de logement CROUS et envoie une notification
push sur ton téléphone (via ntfy.sh) à chaque vérification.
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
            data="Ceci est une notification de test envoyee depuis GitHub Actions. Si tu la recois, tout le circuit fonctionne !".encode("utf-8"),
            headers={
                "Title": "Test crous-watcher OK".encode("utf-8"),
                "Priority": "default",
                "Tags": "white_check_mark",
            },
            timeout=15,
        )
        print("Notification de TEST envoyee.")
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
        title = "Nouveau logement CROUS !"
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
            print(f"Notification envoyee pour : {listing['title']}")
        except Exception as e:
            print(f"Erreur d'envoi ntfy pour {listing['title']}: {e}", file=sys.stderr)


def notify_heartbeat(count_total: int, scope: str):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=f"Verification faite, {count_total} logement(s) au total {scope}. Rien de nouveau.".encode("utf-8"),
            headers={
                "Title": "Crous-watcher : rien de neuf".encode("utf-8"),
                "Priority": "min",
                "Tags": "arrows_counterclockwise",
            },
            timeout=15,
        )
        print("Notification 'rien de nouveau' envoyee.")
    except Exception as e:
        print(f"Erreur d'envoi ntfy (heartbeat) : {e}", file=sys.stderr)


def main():
    search_url = os.environ.get("CROUS_URL") or DEFAULT_SEARCH_URL
    print(f"Verification de : {search_url}")

    listings = fetch_listings(search_url)
    scope = f"({CITY_FILTER})" if CITY_FILTER else "(France entiere)"
    print(f"{len(listings)} logement(s) trouve(s) {scope}.")

    seen = load_seen()
    new_ids = {l["id"] for l in listings} - seen

    if new_ids:
        new_listings = [l for l in listings if l["id"] in new_ids]
        print(f"{len(new_listings)} NOUVELLE(S) offre(s) !")
        notify(new_listings)
    else:
        print("Rien de nouveau.")
        notify_heartbeat(len(listings), scope)

    save_seen({l["id"] for l in listings} | seen)

    if TEST_NOTIFICATION:
        print("Option test activee : envoi d'une notif de test.")
        send_test_notification()


if __name__ == "__main__":
    main()
