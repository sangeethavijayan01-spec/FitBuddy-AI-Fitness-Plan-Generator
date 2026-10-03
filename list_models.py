"""Print Gemini models available to your API key so you can set GEMINI_MODEL.

Usage:  python list_models.py
"""
import sys

from google import genai

from app import config


def main() -> int:
    if not config.api_key_is_configured():
        print("GEMINI_API_KEY is missing. Copy .env.example to .env and add your key first.")
        return 1

    try:
        client = genai.Client(api_key=config.get_gemini_api_key())
        print("Models that support generateContent (use the name in GEMINI_MODEL):\n")
        count = 0
        for model in client.models.list():
            actions = getattr(model, "supported_actions", None) or []
            if actions and "generateContent" not in actions:
                continue
            name = (model.name or "").replace("models/", "")
            display = getattr(model, "display_name", "") or ""
            print(f"  {name:<45} {display}")
            count += 1
        if count == 0:
            print("  (no models returned)")
    except Exception as exc:  # noqa: BLE001 - simple CLI helper
        print(f"Could not list models: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
