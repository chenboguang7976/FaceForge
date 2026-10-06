import re
import string
from pathlib import Path

from faceforge.ui.translations import TRANSLATIONS

SRC = Path(__file__).resolve().parent.parent / "faceforge"
KEY_CALL = re.compile(
    r"(?:\btr|bind_text|bind_tooltip|_caption|SwitchRow|SliderRow|ComboRow|Row|Section|_section|"
    r"Button|Tile|_notify|message\.emit)\((?:[^\"')]*?,\s*)?[\"']([a-z_]+\.[a-z_.0-9]+)[\"']")


def _fields(text):
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


def test_every_key_has_three_languages_with_same_placeholders():
    for key, table in TRANSLATIONS.items():
        assert set(table) == {"en", "zh", "vi"}, key
        assert all(table.values()), key
        assert _fields(table["en"]) == _fields(table["zh"]) == _fields(table["vi"]), key


def test_keys_used_in_code_exist():
    used = set()
    for path in SRC.rglob("*.py"):
        used.update(KEY_CALL.findall(path.read_text("utf-8")))
    used = {k for k in used if not k.endswith((".onnx", ".json", ".py"))}
    missing = sorted(k for k in used if k not in TRANSLATIONS)
    assert not missing, missing


def test_dynamic_keys_exist():
    from faceforge.core.presets import PRESETS

    for name in PRESETS:
        assert f"preset.{name}" in TRANSLATIONS
        assert f"preset.{name}.hint" in TRANSLATIONS
    for profile in ("low", "medium", "high"):
        assert f"profile.{profile}" in TRANSLATIONS
