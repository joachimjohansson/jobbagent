"""Hämtar jobb från Platsbanken (Arbetsförmedlingens öppna API) och sparar en JSON-fil per sida."""
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://jobsearch.api.jobtechdev.se/search"

# En post per sida. Nyckeln är filen som sidan läser.
# Kommunkoder: 1480 Göteborg, 1481 Mölndal, 1402 Partille, 1401 Härryda,
# 1482 Kungälv, 1441 Lerum, 1384 Kungsbacka.
PROFILES = {
    "jobs.json": {
        "searches": [
            "säljingenjör",
            "teknisk säljare",
            "sales engineer",
            "technical sales",
            "innesäljare",
            "inside sales",
        ],
        "municipalities": ["1480", "1481", "1402", "1401", "1482", "1441", "1384"],
    },
    "jobs-kungsbacka.json": {
        "searches": ["dagtid"],
        "municipalities": ["1384"],
    },
}


def fetch(query, municipalities):
    params = [("q", query), ("limit", "100"), ("sort", "pubdate-desc")]
    params += [("municipality", m) for m in municipalities]
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"accept": "application/json", "User-Agent": "jobbagent"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response).get("hits", [])


def build(filename, profile):
    jobs = {}
    failed = 0
    for query in profile["searches"]:
        try:
            hits = fetch(query, profile["municipalities"])
        except Exception as error:
            failed += 1
            print(f"[{filename}] Sökningen '{query}' misslyckades: {error}")
            continue
        print(f"[{filename}] '{query}': {len(hits)} träffar")
        for hit in hits:
            job_id = hit.get("id")
            if job_id in jobs:
                jobs[job_id]["found_by"].append(query)
                continue
            address = hit.get("workplace_address") or {}
            jobs[job_id] = {
                "id": job_id,
                "title": hit.get("headline") or "",
                "employer": (hit.get("employer") or {}).get("name") or "",
                "place": address.get("municipality") or address.get("city") or "",
                "published": (hit.get("publication_date") or "")[:10],
                "deadline": (hit.get("application_deadline") or "")[:10],
                "url": hit.get("webpage_url") or "",
                "source": "Platsbanken",
                "found_by": [query],
            }

    if failed == len(profile["searches"]):
        print(f"[{filename}] Alla sökningar misslyckades, filen lämnas oförändrad.")
        return False

    result = sorted(jobs.values(), key=lambda j: j["published"], reverse=True)
    output = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "jobs": result,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=1)
    print(f"[{filename}] Sparade {len(result)} unika jobb.")
    return True


def main():
    ok = [build(name, profile) for name, profile in PROFILES.items()]
    if not all(ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
