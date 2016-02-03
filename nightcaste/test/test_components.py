"""Tests for base component functionality."""

from nightcaste.components import Component
from nightcaste.components import Position


def test_type():
    """Tests if components return their correct type"""
    component = Component()
    position = Position(42, 3)

    assert component.type() == 'Component'
    assert position.type() == 'Position'
