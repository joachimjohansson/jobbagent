# Uppdatera jobb från e-post (LinkedIn och Jooble)

Körs två gånger per dag av Claude. Läser Gmail och uppdaterar två filer i repot.
Repot är offentligt: lägg aldrig in inloggningslänkar, token eller personuppgifter.

## LinkedIn -> linkedin.json
- Sök i Gmail: `from:jobalerts-noreply@linkedin.com newer_than:3d`
- Hoppa över mejl som bara säger att en avisering stängts av.
- Läs varje mejl i klartext. Varje jobb har titel, företag, ort och en länk `linkedin.com/comm/jobs/view/<id>/...`.
- Spara: `id` (jobb-id), `title`, `company`, `location`, `alert` (söktermen efter "Your job alert for", t.ex. `Säljingenjör`), `received` (mejlets datum), `url` = `https://www.linkedin.com/jobs/view/<id>/` (ta bort allt efter id:t).
- Sidan visar bara aviseringarna i `LI_ALERTS` överst i LinkedIn-delen av `index.html`.

## Jooble -> jooble-epost.json
- Sök i Gmail: `from:subscribe@se.jooble.org newer_than:3d`
- Bara mejl med 🔔 i ämnesraden ("Nya jobbutskick") har jobblistor i klartext. De dagliga sammanställningarna ("Dina dagliga jobbaviseringar") har inga jobb i klartext och hoppas över.
- Varje jobb: titel, länk `https://se.jooble.org/redir/jdp?uid=<uid>&token=...`, ort, företag.
- **Spara aldrig länken eller token.** Ta bara `uid` och bygg `url` = `https://se.jooble.org/desc/<uid>`.
- Spara: `id` (= uid), `title`, `company`, `location`, `alert` (`ckey` i länken: `sales engineer` eller `teknisk säljare`), `received`, `url`.
- Rubriker kan ha fet matematisk Unicode: normalisera med NFKC.

## Gemensamt
- Lägg till nya jobb (nya `id`), ta inte bort gamla förrän de är över 30 dagar. Sätt `updated` till dagens datum.
- Kontrollera att filerna är giltig JSON och att inga `token=` finns: `grep -c token linkedin.json jooble-epost.json` ska ge 0.
- Commit och push till `main`. Rör inte `jobs.json`, den uppdateras av GitHub Actions.
- Sidan slår ihop samma annons från flera källor och visar alla (Platsbanken, LinkedIn, Jooble).
