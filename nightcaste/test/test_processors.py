"""Test module for the event processors."""
import pytest
from nightcaste.entities import EntityConfiguration
from nightcaste.entities import EntityManager
from nightcaste.events import MoveAction
from nightcaste.events import EventManager
from nightcaste.processors import MovementProcessor


@pytest.fixture
def event_manager():
    return EventManager()


@pytest.fixture
def entity_manager():
    return EntityManager()


@pytest.fixture
def simple_config():
    config = EntityConfiguration()
    config.add_attribute('Position', 'x', 42)
    config.add_attribute('Position', 'y', 23)
    config.add_attribute('Renderable', 'character', '@')
    return config


class TestEventProcessor:
    """Nothing to test at the moment"""


class TestMovementProcessor:

    def test_process_event(self, event_manager, entity_manager, simple_config):
        """Tests if an entity's position is changed."""
        processor = MovementProcessor(event_manager, entity_manager)
        entity = entity_manager.create_entity_from_configuration(simple_config)
        event = MoveAction(entity, 1, -1)   # RIGHT-UP

        processor.handle_event(event, 1)
        position = entity_manager.get_entity_component(entity, 'Position')
        assert position.x == 43
        assert position.y == 22
