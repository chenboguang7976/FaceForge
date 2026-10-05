import numpy as np
import pytest
from onnx import TensorProto, helper, save

from faceforge.core import models_data
from faceforge.core.hardware import HardwareInfo
from faceforge.core.models_data import ModelInfo
from faceforge.core.models_processor import ModelMissingError, ModelsProcessor


def _tiny_model(path, op="Add"):
    graph = helper.make_graph(
        [helper.make_node(op, ["x", "x"], ["y"])], "t",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 4])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 4])])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    model.ir_version = 8
    save(model, str(path))
    return path.stat().st_size


@pytest.fixture
def models(tmp_path, monkeypatch):
    registry = dict(models_data.MODELS)
    for i, op in enumerate(["Add", "Mul", "Sub", "Max"]):
        size = _tiny_model(tmp_path / f"m{i}.onnx", op)
        registry[f"m{i}"] = ModelInfo(f"m{i}", f"m{i}.onnx", "", size, "test", f"M{i}")
    monkeypatch.setattr(models_data, "MODELS", registry)
    import faceforge.core.models_processor as mp_module

    monkeypatch.setattr(mp_module, "MODELS", registry)
    hw = HardwareInfo("Test", "CPU", 4, 4, 16384, [], ["CPUExecutionProvider"])
    return ModelsProcessor(tmp_path, device="auto", workers=1, max_loaded=2, hardware=hw)


def test_runs_and_casts_inputs(models):
    out = models.run("m0", {"x": np.ones((1, 4), np.float64)})[0]
    assert out.dtype == np.float32 and out.sum() == 8


def test_lru_eviction_respects_pins(models):
    models.pin(["m0", "m1", "m2"])
    for key in ("m0", "m1", "m2", "m3"):
        models.session(key)
    # Pinned models stay even though the limit is 2; only the unpinned one may go.
    assert {"m0", "m1", "m2"} <= set(models.loaded())
    models.pin([])
    assert len(models.loaded()) == 2


def test_missing_model_raises(models, tmp_path):
    (tmp_path / "m3.onnx").write_bytes(b"truncated")
    assert models.missing(["m0", "m3"]) == ["m3"]
    with pytest.raises(ModelMissingError):
        models.session("m3")


def test_directml_runs_are_serialized(models):
    import threading

    models.session("m0")
    models._session_device["m0"] = "directml"  # pretend it was loaded on DirectML
    inside, overlaps = [0], [0]
    real_run = models._sessions["m0"].run

    class Spy:
        def __getattr__(self, name):
            return getattr(models._sessions_real, name)

    models._sessions_real = models._sessions["m0"]

    def slow_run(*args, **kwargs):
        inside[0] += 1
        if inside[0] > 1:
            overlaps[0] += 1
        import time
        time.sleep(0.02)
        inside[0] -= 1
        return real_run(*args, **kwargs)

    spy = Spy()
    spy.run = slow_run
    models._sessions["m0"] = spy
    threads = [threading.Thread(target=models.run, args=("m0", {"x": np.ones((1, 4), np.float32)}))
               for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert overlaps[0] == 0
