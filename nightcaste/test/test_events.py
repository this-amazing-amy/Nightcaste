"""Tests events. Propably not mutch to do here since events are mostly simple
data transfer objects"""

from nightcaste.events import Event
from nightcaste.events import MoveAction


def test_type():
    """Tests if events return their correct type"""
    event = Event()
    move = MoveAction(42, 1, -1)

    assert event.type() == 'Event'
    assert move.type() == 'MoveAction'
