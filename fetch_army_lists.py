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


def sync_translations(army_lists_data, thematic_categories_data, troop_types_data, battle_cards_data) -> None:
	"""Sync translation.json with names from armyLists, thematicCategories, troopTypes, and battleCards"""
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
	
	# Add army list names and troop option descriptions/notes/core
	if isinstance(army_lists_data, list):
		for army in army_lists_data:
			if not isinstance(army, dict):
				continue
			
			# Add army list name
			name = army.get("name")
			if isinstance(name, str) and name not in existing_keys:
				translations.append({"key": name, "lang_es": ""})
				existing_keys.add(name)
				updated = True
			
			# Add troop option descriptions, notes, and core values
			for troop_option in army.get("troopOptions", []):
				if not isinstance(troop_option, dict):
					continue
				
				# Add description
				description = troop_option.get("description")
				if isinstance(description, str) and description and description not in existing_keys:
					translations.append({"key": description, "lang_es": ""})
					existing_keys.add(description)
					updated = True
				
				# Add note
				note = troop_option.get("note")
				if isinstance(note, str) and note and note not in existing_keys:
					translations.append({"key": note, "lang_es": ""})
					existing_keys.add(note)
					updated = True
				
				# Add core
				core = troop_option.get("core")
				if isinstance(core, str) and core and core not in existing_keys:
					translations.append({"key": core, "lang_es": ""})
					existing_keys.add(core)
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
	
	# Add troop type displayName and description
	if isinstance(troop_types_data, list):
		for troop in troop_types_data:
			if not isinstance(troop, dict):
				continue
			
			# Add displayName
			display_name = troop.get("displayName")
			if isinstance(display_name, str) and display_name not in existing_keys:
				translations.append({"key": display_name, "lang_es": ""})
				existing_keys.add(display_name)
				updated = True
			
			# Add description
			description = troop.get("description")
			if isinstance(description, str) and description not in existing_keys:
				translations.append({"key": description, "lang_es": ""})
				existing_keys.add(description)
				updated = True
	
	# Add battle card displayName and mdText
	if isinstance(battle_cards_data, list):
		for card in battle_cards_data:
			if not isinstance(card, dict):
				continue
			
			# Add displayName
			display_name = card.get("displayName")
			if isinstance(display_name, str) and display_name not in existing_keys:
				translations.append({"key": display_name, "lang_es": ""})
				existing_keys.add(display_name)
				updated = True
			
			# Add mdText
			md_text = card.get("mdText")
			if isinstance(md_text, str) and md_text not in existing_keys:
				translations.append({"key": md_text, "lang_es": ""})
				existing_keys.add(md_text)
				updated = True

	if updated:
		# Sort translations by key for consistency
		translations.sort(key=lambda x: x.get("key", "") if isinstance(x, dict) else "")
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
troop_types = None
battle_cards = None
for output_file, url in ENDPOINTS.items():
	data = fetch_to_file(output_file, url)
	if output_file == "armyLists.json":
		army_lists = data
	elif output_file == "troopTypes.json":
		troop_types = data
	elif output_file == "battleCards.json":
		battle_cards = data

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

# Sync translations with army lists, thematic categories, troop types, and battle cards
sync_translations(army_lists, thematic_categories, troop_types, battle_cards)
