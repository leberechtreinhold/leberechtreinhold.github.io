import logging
import time
import requests
import json
from pathlib import Path

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s",
	datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

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
		log.info("Reading %s", TRANSLATION_FILE)
		t0 = time.perf_counter()
		with TRANSLATION_FILE.open("r", encoding="utf-8") as file:
			translations = json.load(file)
		log.info("  -> loaded %d entries in %.2fs", len(translations), time.perf_counter() - t0)
	else:
		log.info("No existing translation file, starting fresh")
		translations = []

	existing_keys = {
		entry.get("key")
		for entry in translations
		if isinstance(entry, dict) and isinstance(entry.get("key"), str)
	}
	log.info("  -> %d existing keys", len(existing_keys))

	updated = False
	added = 0

	# Add army list names and troop option descriptions/notes/core
	if isinstance(army_lists_data, list):
		log.info("Parsing army lists (%d armies)", len(army_lists_data))
		for army in army_lists_data:
			if not isinstance(army, dict):
				continue
			
			# Add army list name
			name = army.get("name")
			if isinstance(name, str) and name not in existing_keys:
				translations.append({"key": name, "lang_es": ""})
				existing_keys.add(name)
				updated = True
				added += 1
			
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
					added += 1
				
				# Add note
				note = troop_option.get("note")
				if isinstance(note, str) and note and note not in existing_keys:
					translations.append({"key": note, "lang_es": ""})
					existing_keys.add(note)
					updated = True
					added += 1
				
				# Add core
				core = troop_option.get("core")
				if isinstance(core, str) and core and core not in existing_keys:
					translations.append({"key": core, "lang_es": ""})
					existing_keys.add(core)
					updated = True
					added += 1

			# Add homeTopographies values and notes
			for topo in army.get("homeTopographies", []):
				if not isinstance(topo, dict):
					continue

				for value in topo.get("values", []):
					value = value.strip()
					if isinstance(value, str) and value and value not in existing_keys:
						translations.append({"key": value, "lang_es": ""})
						existing_keys.add(value)
						updated = True
						added += 1

				topo_note = topo.get("note")
				if isinstance(topo_note, str) and topo_note and topo_note not in existing_keys:
					translations.append({"key": topo_note, "lang_es": ""})
					existing_keys.add(topo_note)
					updated = True
					added += 1
		log.info("  -> army lists done, %d new keys so far", added)
	
	# Add thematic category names and their army list names
	if isinstance(thematic_categories_data, list):
		log.info("Parsing thematic categories (%d categories)", len(thematic_categories_data))
		section_start = added
		for category in thematic_categories_data:
			# Add category name
			category_name = category.get("name") if isinstance(category, dict) else None
			if isinstance(category_name, str) and category_name not in existing_keys:
				translations.append({"key": category_name, "lang_es": ""})
				existing_keys.add(category_name)
				updated = True
				added += 1
			
			# Add army list names within category
			for army in category.get("armyLists", []):
				army_name = army.get("name") if isinstance(army, dict) else None
				if isinstance(army_name, str) and army_name not in existing_keys:
					translations.append({"key": army_name, "lang_es": ""})
					existing_keys.add(army_name)
					updated = True
					added += 1
		log.info("  -> thematic categories done, %d new keys", added - section_start)
	
	# Add troop type displayName and description
	if isinstance(troop_types_data, list):
		log.info("Parsing troop types (%d types)", len(troop_types_data))
		section_start = added
		for troop in troop_types_data:
			if not isinstance(troop, dict):
				continue
			
			# Add displayName
			display_name = troop.get("displayName")
			if isinstance(display_name, str) and display_name not in existing_keys:
				translations.append({"key": display_name, "lang_es": ""})
				existing_keys.add(display_name)
				updated = True
				added += 1
			
			# Add description
			description = troop.get("description")
			if isinstance(description, str) and description not in existing_keys:
				translations.append({"key": description, "lang_es": ""})
				existing_keys.add(description)
				updated = True
				added += 1
		log.info("  -> troop types done, %d new keys", added - section_start)
	
	# Add battle card displayName and mdText
	if isinstance(battle_cards_data, list):
		log.info("Parsing battle cards (%d cards)", len(battle_cards_data))
		section_start = added
		for card in battle_cards_data:
			if not isinstance(card, dict):
				continue
			
			# Add displayName
			display_name = card.get("displayName")
			if isinstance(display_name, str) and display_name not in existing_keys:
				translations.append({"key": display_name, "lang_es": ""})
				existing_keys.add(display_name)
				updated = True
				added += 1
			
			# Add htmlText
			html_text = card.get("htmlText")
			if isinstance(html_text, str) and html_text not in existing_keys:
				translations.append({"key": html_text, "lang_es": ""})
				existing_keys.add(html_text)
				updated = True
				added += 1
		log.info("  -> battle cards done, %d new keys", added - section_start)

	if updated:
		log.info("Writing %s (%d total keys, %d new)", TRANSLATION_FILE, len(existing_keys), added)
		t0 = time.perf_counter()
		# Sort translations by key for consistency
		translations.sort(key=lambda x: x.get("key", "") if isinstance(x, dict) else "")
		with TRANSLATION_FILE.open("w", encoding="utf-8") as file:
			json.dump(translations, file, indent=4, ensure_ascii=False)
		log.info("  -> written in %.2fs", time.perf_counter() - t0)
	else:
		log.info("No new translation keys found, file unchanged")


def fetch_to_file(output_file: str, url: str) -> None:
	log.info("GET %s", url)
	t0 = time.perf_counter()
	response = requests.get(url)
	elapsed = time.perf_counter() - t0
	response.raise_for_status()
	log.info("  -> %s in %.2fs", response.status_code, elapsed)

	log.info("Parsing response JSON for %s", output_file)
	t0 = time.perf_counter()
	data = response.json()
	log.info("  -> parsed in %.2fs", time.perf_counter() - t0)

	log.info("Writing %s", DB_DIR / output_file)
	with (DB_DIR / output_file).open("w", encoding="utf-8") as file:
		json.dump(data, file, indent=2)

	return data


# Fetch the basic endpoints
army_lists = None
troop_types = None
battle_cards = None
for output_file, url in ENDPOINTS.items():
	log.info("--- Fetching %s ---", output_file)
	data = fetch_to_file(output_file, url)
	if output_file == "armyLists.json":
		army_lists = data
	elif output_file == "troopTypes.json":
		troop_types = data
	elif output_file == "battleCards.json":
		battle_cards = data

# Fetch thematic categories with their army lists
log.info("--- Fetching thematicCategories ---")
log.info("GET https://meshwesh.wgcwar.com/api/v1/thematicCategories")
t0 = time.perf_counter()
response = requests.get("https://meshwesh.wgcwar.com/api/v1/thematicCategories")
elapsed = time.perf_counter() - t0
response.raise_for_status()
log.info("  -> %s in %.2fs", response.status_code, elapsed)
log.info("Parsing response JSON for thematicCategories")
t0 = time.perf_counter()
thematic_categories = response.json()
log.info("  -> parsed in %.2fs", time.perf_counter() - t0)

# For each category, fetch its army lists
log.info("Fetching army lists for %d categories", len(thematic_categories))
for category in thematic_categories:
	category_id = category["id"]
	army_lists_url = f"https://meshwesh.wgcwar.com/api/v1/thematicCategories/{category_id}/armyLists"
	
	try:
		log.info("GET %s", army_lists_url)
		t0 = time.perf_counter()
		army_response = requests.get(army_lists_url)
		elapsed = time.perf_counter() - t0
		army_response.raise_for_status()
		log.info("  -> %s in %.2fs", army_response.status_code, elapsed)
		army_lists_data = army_response.json()
		
		# Extract only name and id from each army
		category["armyLists"] = [
			{"id": army["id"], "name": army["name"]}
			for army in army_lists_data
		]
	except requests.RequestException as e:
		log.error("Error fetching army lists for category %s: %s", category_id, e)
		category["armyLists"] = []

# Save the enriched thematic categories
log.info("Writing %s", DB_DIR / "thematicCategories.json")
with (DB_DIR / "thematicCategories.json").open("w", encoding="utf-8") as file:
	json.dump(thematic_categories, file, indent=2)

# Sync translations with army lists, thematic categories, troop types, and battle cards
log.info("--- Syncing translations ---")
t0 = time.perf_counter()
sync_translations(army_lists, thematic_categories, troop_types, battle_cards)
log.info("  -> done in %.2fs", time.perf_counter() - t0)
