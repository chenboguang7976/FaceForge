from faceforge.diagnose import run_all


def test_native_crash_in_a_case_is_reported_not_fatal(tmp_path):
    report = run_all("unused.mp4", "cpu", tmp_path / "report.txt", timeout=120,
                     cases=[("_crash", "deliberate segfault")])
    text = report.read_text("utf-8")
    assert "exit code: 0 " not in text
    assert "native crash" in text
    assert "no result: crashed" in text
    assert "Fatal Python error" in text  # faulthandler traceback captured from the child
