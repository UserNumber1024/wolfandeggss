from wolfeggs import balance as B


def test_table_has_all_waves():
    assert len(B.WAVE_TABLE) == B.TOTAL_WAVES == 20


def test_endpoints_match_spec():
    assert B.WAVE_TABLE[0][0] == 3.0 and B.WAVE_TABLE[-1][0] == 1.4
    assert B.WAVE_TABLE[0][1] == 1.6 and B.WAVE_TABLE[-1][1] == 0.55


def test_sawtooth_rolls_back_at_stage_start():
    for first in (6, 11, 16):
        prev_peak = B.WAVE_TABLE[first - 2][1]
        assert B.WAVE_TABLE[first - 1][1] > prev_peak  # интервал больше = легче


def test_active_coops_fit_open_rows():
    for n, row in enumerate(B.WAVE_TABLE, start=1):
        stage = (n - 1) // B.WAVES_PER_STAGE + 1
        assert 3 <= row[3] <= 2 * len(B.STAGE_OPEN_ROWS[stage])


def test_min_gap_never_below_one_step():
    assert all(row[2] >= B.HUMAN_STEP_TIME for row in B.WAVE_TABLE)


def test_special_waves_are_fifth_of_stage():
    assert sorted(B.SPECIAL_WAVES) == [5, 10, 15, 20]


def test_new_egg_always_reachable_from_anywhere():
    # инвариант, на котором держится проверка честности в спавнере (spec 5.7)
    min_roll = min(row[0] for row in B.WAVE_TABLE)
    assert B.TELEGRAPH_TIME + min_roll >= 4 * B.HUMAN_STEP_TIME
