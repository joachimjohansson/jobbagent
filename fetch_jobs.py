"""Hämtar jobb från Platsbanken (Arbetsförmedlingens öppna API) och sparar jobs.json."""
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://jobsearch.api.jobtechdev.se/search"

# Sökord. Lägg till eller ta bort rader som du vill.
SEARCHES = [
    "säljingenjör",
    "teknisk säljare",
    "sales engineer",
    "technical sales",
    "innesäljare",
    "inside sales",
]

# Kommunkoder: Göteborg, Mölndal, Partille, Härryda, Kungälv, Lerum, Kungsbacka.
MUNICIPALITIES = ["1480", "1481", "1402", "1401", "1482", "1441", "1384"]


def fetch(query):
    params = [("q", query), ("limit", "100"), ("sort", "pubdate-desc")]
    params += [("municipality", m) for m in MUNICIPALITIES]
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"accept": "application/json", "User-Agent": "jobbagent"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response).get("hits", [])


def main():
    jobs = {}
    failed = 0
    for query in SEARCHES:
        try:
            hits = fetch(query)
        except Exception as error:
            failed += 1
            print(f"Sökningen '{query}' misslyckades: {error}")
            continue
        print(f"'{query}': {len(hits)} träffar")
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

    if failed == len(SEARCHES):
        sys.exit("Alla sökningar misslyckades, jobs.json lämnas oförändrad.")

    result = sorted(jobs.values(), key=lambda j: j["published"], reverse=True)
    output = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "jobs": result,
    }
    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=1)
    print(f"Sparade {len(result)} unika jobb.")


if __name__ == "__main__":
    main()
