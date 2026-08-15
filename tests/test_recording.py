from hybrid_scanner.recording import JsonlRecorder


def test_recorder_closes_and_reports_state(tmp_path):
    path = tmp_path / "events.jsonl"
    recorder = JsonlRecorder(str(path), queue_size=100)
    assert recorder.submit({"ok": True})
    recorder.close()
    state = recorder.snapshot()
    assert state["closed"] is True
    assert state["written"] == 1
    assert path.read_text().strip() == '{"ok":true}'
