name: Uppdatera jobb

on:
  schedule:
    - cron: "0 5 * * *"   # varje morgon, ca 06-07 svensk tid
  workflow_dispatch:       # gör att du kan starta den manuellt

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Hämta jobb
        run: python3 fetch_jobs.py
      - name: Spara ändringar
        run: |
          git config user.name "jobbagent"
          git config user.email "jobbagent@users.noreply.github.com"
          git add "*.json"
          git diff --cached --quiet || (git commit -m "Uppdatera jobb" && git push)
