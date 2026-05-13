from pathlib import Path
import json

from flask import Flask, render_template


BASE_DIR = Path(__file__).resolve().parent


def load_json(filename: str):
        with (BASE_DIR / "db" / filename).open("r", encoding="utf-8") as file:
                return json.load(file)


ARMY_LISTS = load_json("armyLists.json")
TROOP_TYPES = load_json("troopTypes.json")
BATTLE_CARDS = load_json("battleCards.json")
with (BASE_DIR / "translation.json").open("r", encoding="utf-8") as file:
        TRANSLATIONS = json.load(file)
try:
        THEMATIC_CATEGORIES = load_json("thematicCategories.json")
except FileNotFoundError:
        THEMATIC_CATEGORIES = []
TRANSLATION_ES_BY_KEY = {
        entry.get("key"): entry.get("lang_es", "")
        for entry in TRANSLATIONS
        if isinstance(entry, dict) and isinstance(entry.get("key"), str)
}
TRANSLATION_ES_BY_KEY_STRIPPED = {
        key.strip(): value
        for key, value in TRANSLATION_ES_BY_KEY.items()
        if isinstance(key, str) and key.strip()
}
TROOP_TYPE_DISPLAY_BY_CODE = {
        troop.get("permanentCode"): troop.get("displayName", troop.get("permanentCode", ""))
        for troop in TROOP_TYPES
        if troop.get("permanentCode")
}
TROOP_TYPE_COST_BY_CODE = {
        troop.get("permanentCode"): troop.get("cost")
        for troop in TROOP_TYPES
        if troop.get("permanentCode")
}
BATTLE_CARD_DISPLAY_BY_CODE = {
        card.get("permanentCode"): card.get("displayName", card.get("permanentCode", ""))
        for card in BATTLE_CARDS
        if card.get("permanentCode")
}


def build_category_names_by_army_id(categories):
        by_army_id = {}

        for category in categories or []:
                category_name = str(category.get("name", "")).strip()
                if not category_name:
                        continue

                for army in category.get("armyLists", []) or []:
                        army_id = str(army.get("id", "")).strip()
                        if not army_id:
                                continue
                        by_army_id.setdefault(army_id, set()).add(category_name)

        return {
                army_id: sorted(category_names)
                for army_id, category_names in by_army_id.items()
        }


CATEGORY_NAMES_BY_ARMY_ID = build_category_names_by_army_id(THEMATIC_CATEGORIES)

app = Flask(__name__)


def format_year(value, language="en"):
        str_bce = "BC" if language == "en" else "a.C."
        str_ad = "AD" if language == "en" else "d.C."
        if isinstance(value, int):
                if value < 0:
                        return f"{abs(value)} {str_bce}"
                if value > 0:
                        return f"{value} {str_ad}"
                return "0"
        return ""


def translate_to_es(value):
        text = str(value or "")
        translated = TRANSLATION_ES_BY_KEY.get(text)
        if translated:
                return translated

        translated = TRANSLATION_ES_BY_KEY_STRIPPED.get(text.strip())
        if translated:
                return translated

        return text


def find_army_by_id(army_id: str):
        for item in ARMY_LISTS:
                possible_ids = {
                        str(item.get("listId", "")),
                        str(item.get("sortId", "")),
                        str(item.get("id", "")),
                }
                if army_id in possible_ids:
                        return item
        return None


def format_rating_entries(ratings, language="en"):
        formatted = []
        for rating in ratings or []:
                value = rating.get("value")
                if value is None:
                        values = rating.get("values")
                        if values:
                                value = ", ".join(v.strip() for v in values if isinstance(v, str) and v.strip())
                if value is None or value == "":
                        continue
                note = rating.get("note")
                if note:
                        if language == "es":
                                note = translate_to_es(note)
                        formatted.append(f"{value} ({note})")
                else:
                        formatted.append(str(value))
        return ", ".join(formatted) if formatted else "TBD"


def format_battle_card_entries(entries, language="en"):
        if not entries:
                return "-"

        names = []
        for entry in entries:
                code = entry.get("battleCardCode")
                if not code:
                        continue

                name = BATTLE_CARD_DISPLAY_BY_CODE.get(code, code)
                if language == "es":
                        name = translate_to_es(name)
                min_value = entry.get("min")
                max_value = entry.get("max")
                note = entry.get("note")
                if language == "es" and note:
                        note = translate_to_es(note)

                prefix = ""
                if min_value is not None and max_value is not None:
                        prefix = f"{min_value}-{max_value} "

                suffix = f" ({note})" if note else ""
                names.append(f"{prefix}{name}{suffix}")

        return ", ".join(names) if names else "-"


def format_general_troop_entries(entries_for_general, language="en"):
        if not entries_for_general:
                return "None"

        groups = []
        for group in entries_for_general:
                names = []
                for entry in group.get("troopEntries", []):
                        code = entry.get("troopTypeCode")
                        if not code:
                                continue

                        name = TROOP_TYPE_DISPLAY_BY_CODE.get(code, code)
                        note = entry.get("note")
                        if language == "es" and note:
                                note = translate_to_es(note)
                        suffix = f" ({note})" if note else ""
                        names.append(f"{name}{suffix}")

                if names:
                        groups.append(", ".join(names))

        if not groups:
                return "None"

        if len(groups) == 1:
                return groups[0]

        fallback_parts = []
        str_if_possible = "If possible:" if language == "en" else "Si es posible:"
        str_otherwise = "otherwise:" if language == "en" else "en otro caso:"
        for index, group in enumerate(groups):
                if index == 0:
                        fallback_parts.append(f"{str_if_possible} {group}")
                else:
                        fallback_parts.append(f"{str_otherwise} {group}")

        return "; ".join(fallback_parts)


def format_troop_entry_list(entries):
        names_en = []
        names_es = []
        points = []
        for entry in entries or []:
                code = entry.get("troopTypeCode")
                if not code:
                        continue

                name = TROOP_TYPE_DISPLAY_BY_CODE.get(code, code)
                name_es = translate_to_es(name)
                cost = TROOP_TYPE_COST_BY_CODE.get(code)
                note = entry.get("note")
                note_es = translate_to_es(note) if note else ""

                suffix_en = f" ({note})" if note else ""
                suffix_es = f" ({note_es})" if note_es else ""

                names_en.append(f"{name}{suffix_en}")
                names_es.append(f"{name_es}{suffix_es}")
                points.append(str(cost) if cost is not None else "")

        troops_text = " or ".join(names_en) if names_en else "None"
        troops_text_es = " o ".join(names_es) if names_es else translate_to_es("None")
        points_text = " or ".join(points) if points else ""
        return troops_text, troops_text_es, points_text


def format_troop_options(options):
        rows = []
        for option in options or []:
                troops, troops_es, points = format_troop_entry_list(option.get("troopEntries"))

                note_parts = []
                note_parts_es = []
                option_note = option.get("note")
                if option_note:
                        note_parts.append(option_note)
                        note_parts_es.append(translate_to_es(option_note))

                date_ranges = option.get("dateRanges") or []
                if date_ranges:
                        formatted_ranges = []
                        for date_range in date_ranges:
                                start = format_year(date_range.get("startDate"))
                                end = format_year(date_range.get("endDate"))
                                if start and end:
                                        formatted_ranges.append(f"{start} - {end}")
                                elif start:
                                        formatted_ranges.append(start)
                                elif end:
                                        formatted_ranges.append(end)

                        if formatted_ranges:
                                note_parts.append(f"Date ranges: {', '.join(formatted_ranges)}")
                                note_parts_es.append(f"Rango de fechas: {', '.join(formatted_ranges)}")

                battle_line = option.get("core", "")
                description = option.get("description", "")
                note_text = " | ".join(note_parts)
                note_text_es = " | ".join(note_parts_es)

                rows.append(
                        {
                                "min": option.get("min", ""),
                                "max": option.get("max", ""),
                                "battle_line": battle_line,
                                "battle_line_lang_es": translate_to_es(battle_line),
                                "troops": troops,
                                "troops_lang_es": troops_es,
                                "description": description,
                                "description_lang_es": translate_to_es(description),
                                "note": note_text,
                                "note_lang_es": note_text_es,
                                "battle_cards": format_battle_card_entries(option.get("battleCardEntries")),
                                "battle_cards_lang_es": format_battle_card_entries(option.get("battleCardEntries"), language="es"),
                                "points": points,
                        }
                )

        def min_as_number(value):
                if isinstance(value, (int, float)):
                        return value
                try:
                        return int(value)
                except (TypeError, ValueError):
                        return float("-inf")

        rows.sort(
                key=lambda row: (
                        not bool(str(row.get("battle_line", "")).strip()),
                        -min_as_number(row.get("min")),
                )
        )

        return rows


@app.route("/")
def home():
        sorted_army_lists = sorted(
                ARMY_LISTS,
                key=lambda item: item.get("derivedData", {}).get("listStartDate", float("inf")),
        )

        army_rows = []
        for item in sorted_army_lists:
                army_name = str(item.get("name", "Unknown Army")).strip()
                army_id = str(item.get("id", ""))
                army_num = str(item.get("sortId", "")) + str(item.get("sublistId", ""))
                category_names = CATEGORY_NAMES_BY_ARMY_ID.get(army_id, [])
                
                category_en = ", ".join(category_names) or "-"
                category_es = ", ".join(
                        TRANSLATION_ES_BY_KEY.get(cat, cat) for cat in category_names
                ) or "-"
                
                army_rows.append({
                        "army_id": army_id,
                        "army": army_name,
                        "army_lang_es": TRANSLATION_ES_BY_KEY.get(army_name, ""),
                        "army_sort": army_name.lower(),
                        "army_num": army_num,
                        "start_date": format_year(item.get("derivedData", {}).get("listStartDate")),
                        "start_date_lang_es": format_year(item.get("derivedData", {}).get("listStartDate"), language="es"),
                        "start_date_value": item.get("derivedData", {}).get("listStartDate"),
                        "end_date": format_year(item.get("derivedData", {}).get("listEndDate")),
                        "end_date_lang_es": format_year(item.get("derivedData", {}).get("listEndDate"), language="es"),
                        "end_date_value": item.get("derivedData", {}).get("listEndDate"),
                        "category": category_en,
                        "category_lang_es": category_es,
                        "category_sort": category_en.lower(),
                })

        return render_template("triumph_db.html", army_rows=army_rows)


@app.route("/army/<army_id>")
def army_detail(army_id):
        army = find_army_by_id(army_id)

        if army is None:
                return render_template("army_detail.html", army=None, army_id=army_id), 404

        start_date = format_year(army.get("derivedData", {}).get("listStartDate"))
        start_date_lang_es = format_year(army.get("derivedData", {}).get("listStartDate"), language="es")
        end_date = format_year(army.get("derivedData", {}).get("listEndDate"))
        end_date_lang_es = format_year(army.get("derivedData", {}).get("listEndDate"), language="es")
        invasion = format_rating_entries(army.get("invasionRatings"))
        invasion_lang_es = format_rating_entries(army.get("invasionRatings"), language="es")
        maneuver = format_rating_entries(army.get("maneuverRatings"))
        maneuver_lang_es = format_rating_entries(army.get("maneuverRatings"), language="es")
        home_topography = format_rating_entries(army.get("homeTopographies"))
        home_topography_lang_es = format_rating_entries(army.get("homeTopographies"), language="es")
        general_troop_type = format_general_troop_entries(army.get("troopEntriesForGeneral"))
        general_troop_type_lang_es = format_general_troop_entries(army.get("troopEntriesForGeneral"), language="es")
        army_battle_cards = format_battle_card_entries(army.get("battleCardEntries"))
        army_battle_cards_lang_es = format_battle_card_entries(army.get("battleCardEntries"), language="es")
        troop_rows = format_troop_options(army.get("troopOptions"))

        name = army.get("name", "Unknown Army")
        title = name + (f" ({start_date} - {end_date})" if start_date or end_date else "")
        title_lang_es = TRANSLATION_ES_BY_KEY.get(name, "") + (f" ({start_date_lang_es} - {end_date_lang_es})" if start_date_lang_es or end_date_lang_es else "")
        return render_template(
                "army_detail.html",
                army={
                        "name": name,
                        "title": title,
                        "title_lang_es": title_lang_es,
                        "start_date": start_date,
                        "end_date": end_date,
                        "invasion": invasion,
                        "invasion_lang_es": invasion_lang_es,
                        "maneuver": maneuver,
                        "maneuver_lang_es": maneuver_lang_es,
                        "home_topography": home_topography,
                        "home_topography_lang_es": home_topography_lang_es,
                        "general_troop_type": general_troop_type,
                        "general_troop_type_lang_es": general_troop_type_lang_es,
                        "army_battle_cards": army_battle_cards,
                        "army_battle_cards_lang_es": army_battle_cards_lang_es,
                        "troop_rows": troop_rows,
                },
                army_id=army_id,
        )


if __name__ == "__main__":
        app.run(debug=True)
