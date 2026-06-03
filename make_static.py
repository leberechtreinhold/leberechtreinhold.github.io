import shutil
import re
from pathlib import Path
from main import app, ARMY_LISTS, THEMATIC_CATEGORIES

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
# Fix relative links: /army/{id} -> army/{id}.html, /categories/{id} -> categories/{id}.html
html = re.sub(r'href="/army/([^"]+)"', r'href="army/\1.html"', html)
html = re.sub(r'href="/categories/([^"]+)"', r'href="categories/\1.html"', html)
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
    # Fix category links: /categories/{id} -> ../categories/{id}.html
    html = re.sub(r'href="/categories/([^"]+)"', r'href="../categories/\1.html"', html)

    with (army_dir / f"{army_id}.html").open("w", encoding="utf-8") as f:
        f.write(html)

# Create categories list page
response = client.get("/categories")
html = response.data.decode()
# Fix category links: /categories/{id} -> categories/{id}.html
html = re.sub(r'href="/categories/([^"]+)"', r'href="categories/\1.html"', html)
with (docs_dir / "categories.html").open("w", encoding="utf-8") as f:
    f.write(html)

# Create individual category pages
categories_dir = docs_dir / "categories"
categories_dir.mkdir(exist_ok=True)

for category in THEMATIC_CATEGORIES or []:
    category_id = str(category.get("id", ""))
    if not category_id:
        continue
    response = client.get(f"/categories/{category_id}")
    if response.status_code == 404:
        continue

    html = response.data.decode()
    # Fix back link: href="/" -> href="../index.html"
    html = re.sub(r'href="/"', r'href="../index.html"', html)
    # Fix army links: /army/{id} -> ../army/{id}.html
    html = re.sub(r'href="/army/([^"]+)"', r'href="../army/\1.html"', html)
    # Fix sibling category links: /categories/{id} -> {id}.html (same dir)
    html = re.sub(r'href="/categories/([^"]+)"', r'href="\1.html"', html)
    # Fix categories list link: href="/categories" -> href="../categories.html"
    html = re.sub(r'href="/categories"', r'href="../categories.html"', html)

    with (categories_dir / f"{category_id}.html").open("w", encoding="utf-8") as f:
        f.write(html)

total = 1 + len(ARMY_LISTS) + 1 + len(THEMATIC_CATEGORIES or [])
print(f"Generated {total} static HTML files in docs/")
