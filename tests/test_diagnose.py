from faceforge.diagnose import run_all


def test_native_crash_in_a_case_is_reported_not_fatal(tmp_path):
    report = run_all("unused.mp4", "cpu", tmp_path / "report.txt", timeout=120,
                     cases=[("_crash", "deliberate segfault")])
    text = report.read_text("utf-8")
    assert "exit code: 0 " not in text
    assert "native crash" in text
    assert "no result: crashed" in text
    assert "Fatal Python error" in text  # faulthandler traceback captured from the child


def test_diagnostic_always_targets_the_gpu():
    from faceforge.core.hardware import DmlAdapter, GpuInfo, HardwareInfo
    from faceforge.diagnose import diagnostic_device

    laptop = HardwareInfo("Windows 11", "i5-7300HQ", 4, 4, 16384, [GpuInfo("GTX 1050", 4096, 6.1)],
                          ["DmlExecutionProvider", "CPUExecutionProvider"],
                          [DmlAdapter(1, "NVIDIA GeForce GTX 1050", 0x10DE, 4004)])
    assert diagnostic_device(laptop) == "directml"
    cpu_only = HardwareInfo("Linux", "cpu", 4, 4, 8192, [], ["CPUExecutionProvider"])
    assert diagnostic_device(cpu_only) is None


def test_switching_to_cpu_sets_one_worker_on_4_threads(qapp, tmp_path):
    from faceforge.config import Settings
    from faceforge.ui.controller import Controller

    settings = Settings(tmp_path / "settings.json")
    controller = Controller(settings)
    controller.hardware.cpu_threads = 4
    settings.set("execution_workers", 2)
    controller.set_option("device", "cpu")
    assert settings.get("execution_workers") == 1
    controller.shutdown()
