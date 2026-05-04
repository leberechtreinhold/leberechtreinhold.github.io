import shutil
import re
from pathlib import Path
from main import app, ARMY_LISTS

# Remove and create docs folder
docs_dir = Path(__file__).resolve().parent / "docs"
if docs_dir.exists():
    try:
        shutil.rmtree(docs_dir)
    except PermissionError:
        # If docs is locked (for example by a live server), clear HTML files in place.
        for html_file in docs_dir.rglob("*.html"):
            try:
                html_file.unlink()
            except PermissionError:
                pass
docs_dir.mkdir(exist_ok=True)

# Create test client
client = app.test_client()

# Create index.html
response = client.get("/")
html = response.data.decode()
# Fix relative links: /army/{id} -> army/{id}.html
html = re.sub(r'href="/army/([^"]+)"', r'href="army/\1.html"', html)
with (docs_dir / "index.html").open("w", encoding="utf-8") as f:
    f.write(html)

# Create army detail pages
army_dir = docs_dir / "army"
army_dir.mkdir(exist_ok=True)

for army in ARMY_LISTS:
    army_id = army.get("id")
    response = client.get(f"/army/{army_id}")

    html = response.data.decode()
    # Fix back link: href="/" -> href="../index.html"
    html = re.sub(r'href="/"', r'href="../index.html"', html)
    
    with (army_dir / f"{army_id}.html").open("w", encoding="utf-8") as f:
        f.write(html)

print(f"Generated {len(ARMY_LISTS) + 1} static HTML files in docs/")
