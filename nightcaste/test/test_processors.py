"""Test module for the event processors."""
import pytest
from nightcaste.entities import EntityConfiguration
from nightcaste.entities import EntityManager
from nightcaste.events import Event
from nightcaste.events import EventManager
from nightcaste.processors import CollisionManager
from nightcaste.processors import MovementProcessor
from nightcaste.processors import WorldInitializer
from nightcaste.processors import SystemManager
from nightcaste.processors import TurnProcessor
from nightcaste.mapcreation import MapGenerator


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


class TestSystemManager:

    def test_configure(self, event_manager, entity_manager):
        instance = SystemManager(event_manager, entity_manager)
        config = {
            'systems': [
                {
                    'impl': ['nightcaste.processors', 'TurnProcessor'],
                    'config': {'min_turn_time': 0.2}
                },
                {'impl': ['nightcaste.processors', 'WorldInitializer']},
                {'impl': ['nightcaste.processors', 'MovementProcessor']}]}

        assert len(instance.systems) == 0
        instance.configure(config)
        assert isinstance(instance.systems[0], TurnProcessor)
        assert isinstance(instance.systems[1], WorldInitializer)
        assert isinstance(instance.systems[2], MovementProcessor)
        assert instance.systems[0].min_turn_time == 0.2


class TestEventProcessor:
    """Nothing to test at the moment"""


class TestMovementProcessor:

    def test_process_event(self, event_manager, entity_manager, simple_config):
        """Tests if an entity's position is changed."""
        processor = MovementProcessor(event_manager, entity_manager, True)
        entity = entity_manager.new_from_config(simple_config)
        event = Event("MoveAction", {"entity": entity, "dx": 1, "dy": -1})
        # RIGHT-UP
        mg = MapGenerator(entity_manager)
        entity_manager.current_map = mg.create_empty_map(50, 30)

        processor.on_move(event)
        position = entity_manager.get(entity, 'Position')
        assert position.x == 43
        assert position.y == 22


class TestCollisionManager:

    def test_check(self, entity_manager, event_manager):
        conf = EntityConfiguration()
        conf.add_attribute("Position", "x", 0)
        conf.add_attribute("Position", "y", 0)
        b = entity_manager.new_from_blueprint_and_config("tiles.stone_wall",
                                                         conf)
        a = entity_manager.new_from_blueprint_and_config("tiles.stone_wall",
                                                         conf)
        map_config = EntityConfiguration()
        map_config.add_attribute('Map', 'tiles', [[[a, b]]])
        map = entity_manager.new_from_config(map_config)
        cm = CollisionManager(entity_manager, event_manager)

        colliding = cm.check(map, 0, 0)
        assert colliding == [a, b] or colliding == [b, a]
