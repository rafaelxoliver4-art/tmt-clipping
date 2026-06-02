import os, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from url_scraper import scrape_site
from config import DIRECT_SOURCES

valor = [s for s in DIRECT_SOURCES if "valor" in s.get("name","").lower()]
for src in valor:
    try:
        rows = scrape_site(src)
        print(f"\n=== {src['name']} -> {len(rows)} items ===")
        for r in rows[:4]:
            print(f"   [{r.get('published_local','')}] {r.get('title','')[:68]}")
    except Exception as e:
        print(f"\n=== {src['name']} -> ERROR: {e} ===")
