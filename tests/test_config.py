import json

from faceforge.config import DEFAULT_SETTINGS, SETTINGS_VERSION, Settings


def test_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    s = Settings(path)
    assert s.is_new
    s.set("language", "vi")
    s.save()
    again = Settings(path)
    assert not again.is_new
    assert again.get("language") == "vi"
    assert again.get("face_detector_model") == DEFAULT_SETTINGS["face_detector_model"]


def test_v1_settings_are_migrated(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"device": "cuda", "theme": "light", "face_enhancer_model": "GFPGAN 1.4"}))
    s = Settings(path)
    assert s.get("theme") == "light"
    assert s.get("face_enhancer_model") == DEFAULT_SETTINGS["face_enhancer_model"]
    assert s.get("settings_version") == SETTINGS_VERSION


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json")
    assert Settings(path).get("language") == "en"


def test_v2_gpu_index_reset_to_automatic(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"settings_version": 2, "gpu_device_id": 0, "language": "vi",
                                "preset": "quality"}))
    s = Settings(path)
    assert s.get("gpu_device_id") == -1
    assert s.get("language") == "vi" and s.get("preset") == "quality"
