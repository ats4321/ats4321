import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from render_profile import streaks

D = dt.date


def days(counts, start=D(2026, 1, 1)):
    return {(start + dt.timedelta(i)).isoformat(): c for i, c in enumerate(counts)}


def test_streaks():
    today = D(2026, 1, 8)
    # longest run is 3 (Jan 2-4); current run 2 ends yesterday, today's zero doesn't break it
    cur, cur_start, longest, ls, le = streaks(days([0, 1, 2, 3, 0, 0, 1, 1, 0]), today)
    assert (cur, cur_start, longest, ls, le) == (2, D(2026, 1, 7), 3, "2026-01-02", "2026-01-04")
    # a gap before yesterday ends the current streak
    assert streaks(days([1, 0, 0]), D(2026, 1, 3))[0] == 0
    # nothing at all
    assert streaks(days([0, 0]), D(2026, 1, 2))[2] == 0


if __name__ == "__main__":
    test_streaks()
    print("ok")
