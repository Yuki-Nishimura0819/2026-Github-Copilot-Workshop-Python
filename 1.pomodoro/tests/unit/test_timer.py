import pytest

from models.timer import Timer


def test_timer_initialization():
    timer = Timer(1500)

    assert timer.remaining == 1500
    assert timer.initial_seconds == 1500
    assert timer.status == "idle"


def test_timer_tick_when_working():
    timer = Timer(100)
    timer.start()

    remaining = timer.tick()

    assert remaining == 99
    assert timer.remaining == 99


def test_timer_tick_when_paused():
    timer = Timer(100)
    timer.pause()

    remaining = timer.tick()

    assert remaining == 100


def test_timer_reaches_zero_without_negative():
    timer = Timer(1)
    timer.start()

    assert timer.tick() == 0
    assert timer.tick() == 0


def test_timer_reset_restores_initial_state():
    timer = Timer(60)
    timer.start()
    timer.tick()

    timer.reset()

    assert timer.remaining == 60
    assert timer.status == "idle"


def test_timer_rejects_negative_initial_seconds():
    with pytest.raises(ValueError):
        Timer(-1)
