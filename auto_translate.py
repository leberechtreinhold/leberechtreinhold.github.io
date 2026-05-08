import json
import os
import re
import time
from pathlib import Path
from urllib import error, parse, request


BASE_DIR = Path(__file__).resolve().parent
ENV_VARS_FILE = BASE_DIR / "env_vars.bat"
TRANSLATION_FILE = BASE_DIR / "translation.json"
DEEPL_KEY_NAME = "DEEPL_API_KEY"


def load_env_vars_from_bat(file_path: Path) -> None:
	pattern = re.compile(r"^\s*set\s+([^=\s]+)=(.*)$", re.IGNORECASE)

	with file_path.open("r", encoding="utf-8") as file:
		for raw_line in file:
			line = raw_line.strip()
			if not line or line.lower().startswith("rem "):
				continue

			match = pattern.match(line)
			if not match:
				continue

			key, value = match.groups()
			value = value.strip()
			if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
				value = value[1:-1]

			os.environ[key] = value


def get_deepl_api_url(api_key: str) -> str:
	if api_key.endswith(":fx"):
		return "https://api-free.deepl.com/v2/translate"
	return "https://api.deepl.com/v2/translate"


def translate_text(text: str, api_key: str) -> str:
	payload = parse.urlencode(
		{
			"text": text,
			"target_lang": "ES",
		}
	).encode("utf-8")
	api_url = get_deepl_api_url(api_key)
	deepl_request = request.Request(api_url, data=payload, method="POST")
	deepl_request.add_header("Content-Type", "application/x-www-form-urlencoded")
	deepl_request.add_header("Authorization", f"DeepL-Auth-Key {api_key}")

	try:
		with request.urlopen(deepl_request, timeout=30) as response:
			response_data = json.loads(response.read().decode("utf-8"))
	except error.HTTPError as exc:
		error_body = exc.read().decode("utf-8", errors="replace")
		raise RuntimeError(f"DeepL request failed with status {exc.code}: {error_body}") from exc
	except error.URLError as exc:
		raise RuntimeError(f"DeepL request failed: {exc.reason}") from exc

	translations = response_data.get("translations", [])
	if not translations or "text" not in translations[0]:
		raise RuntimeError(f"Unexpected DeepL response: {response_data}")

	return translations[0]["text"]


def main() -> None:
	if not ENV_VARS_FILE.exists():
		raise FileNotFoundError(f"Missing env vars file: {ENV_VARS_FILE}")
	if not TRANSLATION_FILE.exists():
		raise FileNotFoundError(f"Missing translation file: {TRANSLATION_FILE}")

	load_env_vars_from_bat(ENV_VARS_FILE)
	api_key = os.environ.get(DEEPL_KEY_NAME)
	if not api_key:
		raise RuntimeError(f"{DEEPL_KEY_NAME} not found in {ENV_VARS_FILE}")

	with TRANSLATION_FILE.open("r", encoding="utf-8") as file:
		translations = json.load(file)

	updated = False
	translated_count = 0
	for entry in translations:
		if not isinstance(entry, dict):
			continue

		key = entry.get("key")
		lang_es = entry.get("lang_es")
		if not isinstance(key, str) or lang_es != "":
			continue

		translated_text = translate_text(key, api_key)
		entry["lang_es"] = translated_text
		updated = True
		translated_count += 1
		print(f"Translated: {key} -> {translated_text}")
		time.sleep(0.25)

	if updated:
		with TRANSLATION_FILE.open("w", encoding="utf-8") as file:
			json.dump(translations, file, indent=4, ensure_ascii=False)

	print(f"Completed. Updated {translated_count} entr{'y' if translated_count == 1 else 'ies'}.")


if __name__ == "__main__":
	main()