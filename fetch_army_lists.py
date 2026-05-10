import requests
import json
from pathlib import Path

ENDPOINTS = {
	"armyLists.json": "https://meshwesh.wgcwar.com/api/v1/armyLists?summary=false",
	"troopTypes.json": "https://meshwesh.wgcwar.com/api/v1/troopTypes",
	"battleCards.json": "https://meshwesh.wgcwar.com/api/v1/battleCards",
}

DB_DIR = Path(__file__).resolve().parent / "db"
DB_DIR.mkdir(exist_ok=True)
TRANSLATION_FILE = Path(__file__).resolve().parent / "translation.json"


def sync_translations(army_lists_data, thematic_categories_data) -> None:
	"""Sync translation.json with names from both armyLists and thematicCategories"""
	if TRANSLATION_FILE.exists():
		with TRANSLATION_FILE.open("r", encoding="utf-8") as file:
			translations = json.load(file)
	else:
		translations = []

	existing_keys = {
		entry.get("key")
		for entry in translations
		if isinstance(entry, dict) and isinstance(entry.get("key"), str)
	}

	updated = False
	
	# Add army list names
	if isinstance(army_lists_data, list):
		for army in army_lists_data:
			name = army.get("name") if isinstance(army, dict) else None
			if isinstance(name, str) and name not in existing_keys:
				translations.append({"key": name, "lang_es": ""})
				existing_keys.add(name)
				updated = True
	
	# Add thematic category names and their army list names
	if isinstance(thematic_categories_data, list):
		for category in thematic_categories_data:
			# Add category name
			category_name = category.get("name") if isinstance(category, dict) else None
			if isinstance(category_name, str) and category_name not in existing_keys:
				translations.append({"key": category_name, "lang_es": ""})
				existing_keys.add(category_name)
				updated = True
			
			# Add army list names within category
			for army in category.get("armyLists", []):
				army_name = army.get("name") if isinstance(army, dict) else None
				if isinstance(army_name, str) and army_name not in existing_keys:
					translations.append({"key": army_name, "lang_es": ""})
					existing_keys.add(army_name)
					updated = True

	if updated:
		with TRANSLATION_FILE.open("w", encoding="utf-8") as file:
			json.dump(translations, file, indent=4, ensure_ascii=False)


def fetch_to_file(output_file: str, url: str) -> None:
	response = requests.get(url)
	response.raise_for_status()
	data = response.json()

	with (DB_DIR / output_file).open("w", encoding="utf-8") as file:
		json.dump(data, file, indent=2)

	return data


# Fetch the basic endpoints
army_lists = None
for output_file, url in ENDPOINTS.items():
	data = fetch_to_file(output_file, url)
	if output_file == "armyLists.json":
		army_lists = data

# Fetch thematic categories with their army lists
response = requests.get("https://meshwesh.wgcwar.com/api/v1/thematicCategories")
response.raise_for_status()
thematic_categories = response.json()

# For each category, fetch its army lists
for category in thematic_categories:
	category_id = category["id"]
	army_lists_url = f"https://meshwesh.wgcwar.com/api/v1/thematicCategories/{category_id}/armyLists"
	
	try:
		army_response = requests.get(army_lists_url)
		army_response.raise_for_status()
		army_lists_data = army_response.json()
		
		# Extract only name and id from each army
		category["armyLists"] = [
			{"id": army["id"], "name": army["name"]}
			for army in army_lists_data
		]
	except requests.RequestException as e:
		print(f"Error fetching army lists for category {category_id}: {e}")
		category["armyLists"] = []

# Save the enriched thematic categories
with (DB_DIR / "thematicCategories.json").open("w", encoding="utf-8") as file:
	json.dump(thematic_categories, file, indent=2)

# Sync translations with both army lists and thematic categories
sync_translations(army_lists, thematic_categories)
