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

## Arkivera mejlen efter genomgång
- När filerna är uppdaterade (och pushen lyckats) arkiveras alla LinkedIn- och Jooble-mejl som gåtts igenom: ta bort etiketten `INBOX` från tråden (`unlabel_thread` med `labelIds: ["INBOX"]`). Ta inte bort `UNREAD` och radera inget.
- Gäller bara trådar från `jobalerts-noreply@linkedin.com` och `subscribe@se.jooble.org` som ingick i dagens sökningar, inklusive Joobles dagliga sammanställningar och LinkedIn-mejl om stängda aviseringar.
- Om uppdateringen eller pushen misslyckas arkiveras inget, så att mejlen tas med vid nästa körning.
- Rör aldrig mejl från andra avsändare här (ansökningssvar hanteras separat).

## Gemensamt
- Lägg till nya jobb (nya `id`), ta inte bort gamla förrän de är över 30 dagar. Sätt `updated` till dagens datum.
- Kontrollera att filerna är giltig JSON och att inga `token=` finns: `grep -c token linkedin.json jooble-epost.json` ska ge 0.
- Commit och push till `main`. Rör inte `jobs.json`, den uppdateras av GitHub Actions.
- Sidan slår ihop samma annons från flera källor och visar alla (Platsbanken, LinkedIn, Jooble).

# Svar på ansökningar -> applications.json

Körs tre gånger per dag av Claude (schemalagd uppgift "Bevaka ansökningsmejl"). Startsidan visar Att göra, Läget, Arkiv och månadsrapporten från den här filen.

## Integritet (repot är offentligt)
- Spara bara: företag, tjänst, ort, status, datum, länkar till annonsen och ansökningssidan samt korta neutrala händelser.
- Spara aldrig: namn på personer, mejladresser, telefonnummer, citat ur mejl, inloggnings- eller kandidatlänkar, löneuppgifter eller anteckningar.

## Fält per ansökan
- `id` (fast, t.ex. `solar-teknisk-innesaljare`), `company`, `role`, `place`, `deadline`, `created`, `ad_url`, `apply_url`, `job_ids` (Platsbanken-id, döljer jobbet bland Nya jobb).
- `status`: `att-skicka`, `skickad`, `bekraftad`, `intervju`, `erbjudande`, `avslag`, `tackat-nej` eller `avslutad`. De tre sista hamnar i arkivet.
- `applied` (datum då ansökan skickades, `null` om okänt; då kan `applied_month` = `ÅÅÅÅ-MM` anges för månadsrapporten).
- `todo`: korta steg som visas under Att göra. Töm listan när ansökan är skickad.
- `events`: `{ "date": "ÅÅÅÅ-MM-DD", "text": "..." }` i tidsordning. Den sista händelsen visas som senaste läget.

## Så uppdateras filen
- Sök i Gmail: `newer_than:2d in:anywhere -from:linkedin.com -from:jooble.org` och matcha mot företagen i filen (avsändardomän, företagsnamn, tjänst eller rekryteringsfirma). Rekryteringssystem som ReachMee, SuccessFactors, Heartpace, Ponty, Teamtailor, Varbi och Jobylon räknas till företaget som nämns i mejlet.
- Bekräftelse på mottagen ansökan: `status` = `bekraftad` (om den var `att-skicka` eller `skickad`), sätt `applied` till mejlets datum om det saknas, töm `todo`, lägg till händelsen "Bekräftelse mottagen".
- Kallelse till intervju eller test: `status` = `intervju`, händelse "Intervju <datum och tid>" eller "Inbjudan till test". Okänt datum: "Inbjudan till intervju".
- Avslag: `status` = `avslag`, händelse "Avslag". Erbjudande: `status` = `erbjudande`.
- Lägg aldrig till samma händelse två gånger. Sätt `updated` till dagens datum när något ändrats.
- Kontrollera att filen är giltig JSON och följer integritetsreglerna, committa och pusha till `main`.
