"""Hämtar jobb från Platsbanken och Jooble och sparar en JSON-fil per sida.

Jooble-nyckeln läses från miljövariabeln JOOBLE_API_KEY (GitHub-hemligheten).
Skriv aldrig nyckeln i den här filen, eftersom repot är offentligt.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PLATSBANKEN = "https://jobsearch.api.jobtechdev.se/search"
JOOBLE = "https://jooble.org/api/"

# En post per sida. Nyckeln är filen som sidan läser.
# Kommunkoder: 1480 Göteborg, 1481 Mölndal, 1402 Partille, 1401 Härryda,
# 1482 Kungälv, 1441 Lerum, 1384 Kungsbacka.
# "jooble" tas bort om du inte vill ha Jooble på sidan. Radie i km: 4, 8, 16, 26, 40 eller 80.
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
        "jooble": {"location": "Göteborg", "radius": "26"},
    },
    "jobs-kungsbacka.json": {
        "searches": ["dagtid"],
        "municipalities": ["1384"],
        "jooble": {"location": "Kungsbacka", "radius": "16"},
    },
}


def clean(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def platsbanken(query, municipalities):
    params = [("q", query), ("limit", "100"), ("sort", "pubdate-desc")]
    params += [("municipality", m) for m in municipalities]
    req = urllib.request.Request(
        PLATSBANKEN + "?" + urllib.parse.urlencode(params),
        headers={"accept": "application/json", "User-Agent": "jobbagent"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response).get("hits", [])


def jooble(key, query, location, radius):
    body = json.dumps({"keywords": query, "location": location, "radius": radius}).encode()
    req = urllib.request.Request(
        JOOBLE + key,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "jobbagent"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response).get("jobs", [])


def same_job(job):
    return (job["title"].lower(), job["employer"].lower())


def build(filename, profile):
    jobs = {}
    seen = set()
    failed = 0

    for query in profile["searches"]:
        try:
            hits = platsbanken(query, profile["municipalities"])
        except Exception as error:
            failed += 1
            print(f"[{filename}] Platsbanken '{query}' misslyckades: {error}")
            continue
        print(f"[{filename}] Platsbanken '{query}': {len(hits)} träffar")
        for hit in hits:
            job_id = hit.get("id")
            if job_id in jobs:
                jobs[job_id]["found_by"].append(query)
                continue
            address = hit.get("workplace_address") or {}
            job = {
                "id": job_id,
                "title": clean(hit.get("headline")),
                "employer": clean((hit.get("employer") or {}).get("name")),
                "place": address.get("municipality") or address.get("city") or "",
                "published": (hit.get("publication_date") or "")[:10],
                "deadline": (hit.get("application_deadline") or "")[:10],
                "url": hit.get("webpage_url") or "",
                "source": "Platsbanken",
                "found_by": [query],
            }
            jobs[job_id] = job
            seen.add(same_job(job))

    if failed == len(profile["searches"]):
        print(f"[{filename}] Alla Platsbanken-sökningar misslyckades, filen lämnas oförändrad.")
        return False

    settings = profile.get("jooble")
    key = os.environ.get("JOOBLE_API_KEY", "").strip()
    if settings and not key:
        print(f"[{filename}] Ingen JOOBLE_API_KEY hittades, hoppar över Jooble.")
    elif settings:
        for query in profile["searches"]:
            try:
                hits = jooble(key, query, settings["location"], settings["radius"])
            except Exception as error:
                print(f"[{filename}] Jooble '{query}' misslyckades: {error}")
                continue
            added = 0
            for hit in hits:
                job = {
                    "id": "jooble-" + str(hit.get("id") or hit.get("link")),
                    "title": clean(hit.get("title")),
                    "employer": clean(hit.get("company")),
                    "place": clean(hit.get("location")),
                    "published": (hit.get("updated") or "")[:10],
                    "deadline": "",
                    "url": hit.get("link") or "",
                    "source": "Jooble",
                    "found_by": [query],
                }
                if not job["url"]:
                    continue
                if same_job(job) in seen:
                    continue  # samma annons finns redan (ofta från Platsbanken)
                seen.add(same_job(job))
                jobs[job["id"]] = job
                added += 1
            print(f"[{filename}] Jooble '{query}': {len(hits)} träffar, {added} nya")

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
