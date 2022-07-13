from unittest.mock import MagicMock

from p2p.infrastructure.repository.bin_auth import JigSawSolver


def test_get_track():
    driver = MagicMock()
    s = JigSawSolver(driver=driver)

    track = s.get_track(176, current=60)
    assert len(track) > 0
    assert all([i >= 0 for i in track])
    assert abs(sum(track) - 116) < 2

    track = s.get_track(100)
    assert len(track) > 0
    assert all([i >= 0 for i in track])
    assert abs(sum(track) - 100) < 2

    track = s.get_track(100, 150)
    assert len(track) > 0
    assert all([i <= 0 for i in track])
    assert abs(sum(track) + 50) < 2
