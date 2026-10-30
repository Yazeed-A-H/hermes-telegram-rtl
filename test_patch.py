"""Checks the plugin's wraps on the real TelegramAdapter class (no gateway, no network).

Run with the Hermes interpreter after every `hermes update`:
  $(hermes --print-runtime-command | python3 -c "import json,sys;print(json.load(sys.stdin)[0])") test_patch.py
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))
import hermes_bootstrap  # noqa: F401,E402  (adds Hermes's managed site-packages)

spec = importlib.util.spec_from_file_location("telegram_rtl", os.path.join(HERE, "__init__.py"), submodule_search_locations=[HERE])
plug = importlib.util.module_from_spec(spec); sys.modules["telegram_rtl"] = plug; spec.loader.exec_module(plug)
from plugins.platforms.telegram.adapter import TelegramAdapter as C  # noqa: E402

# Arabic detection: >= 30% Arabic letters outside code
assert plug._ar("مرحبا يا Hermes")
assert not plug._ar("Weather update for القاهرة: sunny, 31 degrees, light wind.")
assert plug._ar("الـ Plugin جاهز ومجرّب، ويحتاج `/restart` منك")
assert plug._ar("شغّل هذا الأمر:\n```bash\nhermes plugins enable telegram-rtl && hermes gateway restart\n```")
assert not plug._ar("") and not plug._ar(None) and not plug._ar("hello")

plug._patch(C); first = C._rich_message_payload; plug._patch(C)
assert C._rich_message_payload is first, "patched twice"
a = object.__new__(C)
p = C._rich_message_payload(a, "مرحبا\nسطر")
assert p["is_rtl"] is True and "\u200f" not in p["markdown"], p  # rich: flag only, text untouched
assert "is_rtl" not in C._rich_message_payload(a, "hello")
assert "is_rtl" not in C._rich_message_payload(a, "Weather update for القاهرة: sunny, 31 degrees, light wind.")
assert C._needs_rich_rendering(a, "مرحبا") is True
assert C._needs_rich_rendering(a, "hello") is False
assert C._needs_rich_rendering(a, "|a|b|\n|---|---|\n|1|2|") is True  # original behaviour kept
assert "\u200f" in C.format_message(a, "- مرحبا Outlook")
assert "\u200f" not in C.format_message(a, "- hello")
print("ok")
