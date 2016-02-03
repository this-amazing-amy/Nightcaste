"""Tests for base component functionality."""

import pytest
from nightcaste.components import Component
from nightcaste.components import Position
from nightcaste.components import ComponentManager


@pytest.fixture
def component_manager():
    return ComponentManager()


def test_add_component(component_manager):
    """Tests if components are added to the manager correctly"""
    id = 1
    component = Component()
    component_manager.add_component(id, component)
    assert 'Component' in component_manager.components
    assert 1 in component_manager.components['Component']
    assert component_manager.components['Component'][1] == component


def test_type():
    """Tests if components return their correct type"""
    component = Component()
    position = Position(42, 3)

    assert component.type() == 'Component'
    assert position.type() == 'Position'
