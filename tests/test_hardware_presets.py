import pytest

from faceforge.core import hardware, presets
from faceforge.core.hardware import GpuInfo, HardwareInfo


def machine(ram_gb, vram_gb=None, cc=6.1, providers=("CUDAExecutionProvider", "DmlExecutionProvider",
                                                      "CPUExecutionProvider")):
    gpus = [GpuInfo("GPU", int(vram_gb * 1024), cc)] if vram_gb else []
    return HardwareInfo("Windows 11", "CPU", 4, 4, int(ram_gb * 1024), gpus, list(providers))


@pytest.fixture
def lite(monkeypatch):
    monkeypatch.setenv("FACEFORGE_EDITION", "lite")


@pytest.fixture
def pro(monkeypatch):
    monkeypatch.setenv("FACEFORGE_EDITION", "pro")


def test_gtx1050_16gb_is_low_profile_but_balanced_in_lite(lite):
    gtx1050 = machine(16, 4, 6.1)
    assert hardware.classify(gtx1050) == hardware.PROFILE_LOW
    assert presets.default_preset(gtx1050) == presets.PRESET_BALANCED
    assert hardware.runtime_settings(gtx1050, "directml")["max_loaded_models"] == 4


def test_8gb_ram_falls_back_to_fast_preset(lite):
    assert presets.default_preset(machine(8, 4, 6.1)) == presets.PRESET_PERFORMANCE


def test_pro_defaults_and_requirements(pro):
    rtx = machine(32, 12, 8.9)
    assert hardware.classify(rtx) == hardware.PROFILE_HIGH
    assert presets.default_preset(rtx) == presets.PRESET_MAXIMUM
    assert presets.meets_pro_requirements(rtx)
    assert not presets.meets_pro_requirements(machine(16, 4, 6.1))


def test_fp16_only_on_fast_half_precision_gpus():
    pascal, ampere = machine(16, 4, 6.1), machine(32, 12, 8.6)
    assert presets.preset_settings("performance", pascal, "cuda")["face_swapper_model"] == "inswapper_128"
    assert presets.preset_settings("performance", ampere, "cuda")["face_swapper_model"] == "inswapper_128_fp16"
    assert presets.preset_settings("performance", ampere, "cpu")["face_swapper_model"] == "inswapper_128"


def test_cuda13_is_not_used_on_pascal(monkeypatch):
    monkeypatch.setattr(hardware, "_ort_version", lambda: (1, 30))
    assert not machine(16, 4, 6.1).has_cuda
    assert hardware.resolve_device("auto", machine(16, 4, 6.1)) == "directml"
    assert machine(32, 12, 8.6).has_cuda
    monkeypatch.setattr(hardware, "_ort_version", lambda: (1, 24))
    assert machine(16, 4, 6.1).has_cuda


def test_resolve_device_falls_back_to_available():
    cpu_only = machine(8, None, providers=("CPUExecutionProvider",))
    assert hardware.resolve_device("cuda", cpu_only) == "cpu"
    assert hardware.resolve_device("auto", cpu_only) == "cpu"


def test_presets_only_touch_preset_keys():
    for name in presets.PRESETS:
        values = presets.preset_settings(name, machine(16, 4), "directml")
        assert set(values) == set(presets.PRESET_KEYS)


def test_dml_prefers_discrete_gpu_on_dual_gpu_laptops():
    from faceforge.core.hardware import DmlAdapter, pick_dml_adapter

    intel = DmlAdapter(0, "Intel(R) HD Graphics 630", 0x8086, 128)
    nvidia = DmlAdapter(1, "NVIDIA GeForce GTX 1050", 0x10DE, 4096)
    basic = DmlAdapter(2, "Microsoft Basic Render Driver", 0x1414, 0, software=True)
    assert pick_dml_adapter([intel, nvidia, basic]) is nvidia
    assert pick_dml_adapter([intel, basic]) is intel
    assert pick_dml_adapter([basic]) is None


def test_models_processor_uses_best_dml_adapter_unless_overridden(tmp_path):
    from faceforge.core.hardware import DmlAdapter
    from faceforge.core.models_processor import ModelsProcessor

    hw = machine(16, 4, 6.1, providers=("DmlExecutionProvider", "CPUExecutionProvider"))
    hw.dml_adapters = [DmlAdapter(0, "Intel(R) HD Graphics 630", 0x8086, 128),
                       DmlAdapter(1, "NVIDIA GeForce GTX 1050", 0x10DE, 4096)]
    mp = ModelsProcessor(tmp_path, device="directml", gpu_device_id=-1, hardware=hw)
    assert mp.device == "directml"
    assert mp._providers("directml")[0] == ("DmlExecutionProvider", {"device_id": 1})
    assert mp.adapter_name == "NVIDIA GeForce GTX 1050"
    mp.configure("directml", 2, 3, gpu_device_id=0)
    assert mp._providers("directml")[0][1]["device_id"] == 0
