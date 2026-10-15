from wolfeggs.save import SaveData, load, record_result, store


def test_roundtrip(tmp_path):
    p = tmp_path / "s.json"
    d = SaveData(best_score=42, fullscreen=True)
    store(d, p)
    assert load(p) == d


def test_missing_file(tmp_path):
    assert load(tmp_path / "nope.json") == SaveData()


def test_load_garbage(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{not json", encoding="utf-8")
    assert load(p) == SaveData()


def test_load_wrong_types(tmp_path):
    p = tmp_path / "s.json"
    p.write_text('{"best_score": "lots", "music_volume": 7, "extra": 1}', encoding="utf-8")
    d = load(p)
    assert d.best_score == 0 and d.music_volume == 1.0


def test_record_result():
    d = SaveData(best_score=10)
    assert record_result(d, 12, 7, 20) is True and d.best_wave == 7
    assert record_result(d, 5, 3, 1) is False and d.best_score == 12
