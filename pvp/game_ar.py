"""AR game logic for PvP - shared with ar app where applicable."""
import random

ROULETTE_WHEEL = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]


def wheel_neighbors(center):
    """Return (ccw2, ccw1, cw1, cw2) for center on wheel."""
    try:
        idx = ROULETTE_WHEEL.index(center)
    except ValueError:
        return (None, None, None, None)
    n = len(ROULETTE_WHEEL)
    ccw2 = ROULETTE_WHEEL[(idx - 2) % n]
    ccw1 = ROULETTE_WHEEL[(idx - 1) % n]
    cw1 = ROULETTE_WHEEL[(idx + 1) % n]
    cw2 = ROULETTE_WHEEL[(idx + 2) % n]
    return (ccw2, ccw1, cw1, cw2)


def generate_ar_neighbors_state():
    """Generate center and neighbors for AR Neighbors PvP round."""
    center = random.randint(0, 36)
    ccw2, ccw1, cw1, cw2 = wheel_neighbors(center)
    return {
        'center': center,
        'ccw2': ccw2, 'ccw1': ccw1, 'cw1': cw1, 'cw2': cw2,
    }


def check_ar_neighbors_answer(cell1, cell2, cell4, cell5, center):
    """Check if answer is correct (clockwise = strict). Returns (ok, expected_tuple)."""
    ccw2, ccw1, cw1, cw2 = wheel_neighbors(center)
    expected = (ccw2, ccw1, cw1, cw2)

    def to_int(v):
        try:
            return int(v) if v is not None and str(v).strip() != '' else None
        except (TypeError, ValueError):
            return None

    u1, u2, u4, u5 = to_int(cell1), to_int(cell2), to_int(cell4), to_int(cell5)
    user = (u1, u2, u4, u5)
    ok = user == expected
    return ok, expected
