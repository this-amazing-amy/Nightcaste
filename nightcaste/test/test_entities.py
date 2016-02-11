import pytest
from nightcaste.entities import EntityManager
from nightcaste.entities import EntityConfiguration
from nightcaste.entities import ComponentManager
import nightcaste.components as components


@pytest.fixture
def component_manager():
    return ComponentManager()


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


class TestEntityManager:

    def test_create_entity(self, entity_manager):
        entity1 = entity_manager.create_entity()
        entity2 = entity_manager.create_entity()

        assert entity1 is not None
        assert entity2 is not None
        assert entity1 != entity2

    def test_new_from_config(
            self, entity_manager, simple_config):
        entity = entity_manager.new_from_config(simple_config)
        position = entity_manager.get_entity_component(entity, 'Position')
        renderable = entity_manager.get_entity_component(entity, 'Renderable')
        assert entity is not None
        assert position is not None
        assert renderable is not None
        assert position.x == 42
        assert position.y == 23
        assert renderable.character == '@'

    def test_new_from_blueprint(self, entity_manager):
        player = entity_manager.new_from_blueprint('game.player')
        assert player is not None
        renderable = entity_manager.get_entity_component(player, 'Renderable')
        assert renderable is not None
        assert renderable.character == '@'
        assert renderable.z_index == 9

    def test_create_from_blueprint_and_config(self, entity_manager):
        config = EntityConfiguration()
        config.add_attribute('Position', 'x', 42)
        config.add_attribute('Position', 'y', 27)
        player = entity_manager.new_from_blueprint_and_config(
            'game.player', config)
        assert player is not None
        renderable = entity_manager.get_entity_component(player, 'Renderable')
        position = entity_manager.get_entity_component(player, 'Position')
        assert position is not None
        assert renderable is not None
        assert position.x == 42
        assert position.y == 27
        assert renderable.character == '@'
        assert renderable.z_index == 9

    def test_destroy_entity(self, entity_manager, simple_config):
        entity = entity_manager.new_from_config(simple_config)
        entity_manager.destroy_entity(entity)
        assert entity_manager.get_entity_component(entity, 'Position') is None
        assert entity_manager.get_entity_component(entity, 'Renderable') is None

    def test_get_entity_component(self, entity_manager, simple_config):
        entity = entity_manager.new_from_config(simple_config)
        position = entity_manager.get_entity_component(entity, 'Position')
        renderable = entity_manager.get_entity_component(entity, 'Renderable')
        assert position is not None
        assert renderable is not None

    def test_get_all_of_type(self, entity_manager, simple_config):
        entity_manager.new_from_config(simple_config)
        entity_manager.new_from_config(simple_config)
        positions = entity_manager.get_all_of_type('Position')
        renderables = entity_manager.get_all_of_type('Renderable')
        assert len(positions) > 1
        assert len(renderables) > 1
        for position in positions.itervalues():
            assert position.type() == 'Position'
        for renderable in renderables.itervalues():
            assert renderable.type() == 'Renderable'

    def test_get_components_for_entites(
            self, entity_manager, simple_config):
        entity = entity_manager.new_from_config(simple_config)
        positions = entity_manager.get_all_of_type('Position')
        renderables = entity_manager.get_components_for_entities(
            positions, 'Renderable')
        assert renderables[entity].character == '@'


class TestComponentManager:

    def test_add_component(self, component_manager):
        """Tests if components are added to the manager correctly."""
        id = 1
        component = components.Component()
        component_manager.add_component(id, component)
        assert 'Component' in component_manager.components
        assert 1 in component_manager.components['Component']
        assert component_manager.components['Component'][1] == component

    def test_add_components_by_configuration(self, component_manager):
        """Tests if the Component Manager can create components by
        configuration."""
        config = EntityConfiguration()
        config.add_attribute('Position', 'x', 42)
        config.add_attribute('Position', 'y', 27)
        component_manager.add_components(2, config)
        assert 'Position' in component_manager.components
        assert 2 in component_manager.components['Position']

        position = component_manager.components['Position'][2]
        assert position.x == 42
        assert position.y == 27

    def test_get_component(self, component_manager):
        """Tests retrieving a component."""
        component = components.Component()
        component_manager.add_component(3, component)
        assert component_manager.get_component(
            3, component.type()) == component

    def test_remove_component(self, component_manager):
        """Tests removing a single component."""
        component1 = components.Component()
        component2 = components.Position()
        component_manager.add_component(4, component1)
        component_manager.add_component(4, component2)

        component_manager.remove_component(4, component1.type())
        assert component_manager.get_component(4, component1.type()) is None
        assert component_manager.get_component(
            4, component2.type()) == component2

        component_manager.remove_component(4, component2.type())
        assert component_manager.get_component(4, component2.type()) is None

    def test_remove_components(self, component_manager):
        """Tests removing all compoennts of an entity."""
        component1 = components.Component()
        component2 = components.Position()
        component_manager.add_component(5, component1)
        component_manager.add_component(5, component2)

        component_manager.remove_components(5)
        assert component_manager.get_component(5, component1.type()) is None
        assert component_manager.get_component(5, component2.type()) is None


class TestEntityConfiguration:

    def test_add_component(self):
        config = EntityConfiguration()
        config.add_component('Renderable')
        assert config.get_attributes('Renderable') == {}
        config.add_attribute('Position', 'x', 42)
        config.add_attribute('Position', 'y', 27)
        config.add_component('Position')
        assert config.get_attributes('Position') == {'x': 42, 'y': 27}

    def test_add_attribute(self):
        config = EntityConfiguration()
        config.add_attribute('Position', 'x', 42)
        assert config.get_attributes('Position') == {'x': 42}
        config.add_attribute('Position', 'y', 27)
        assert config.get_attributes('Position') == {'x': 42, 'y': 27}

    def test_get_attribute(self, simple_config):
        assert simple_config.get_attributes('Renderable') == {'character': '@'}
        assert simple_config.get_attributes('Position') == {'x': 42, 'y': 23}

    def test_update(self):
        config = EntityConfiguration()
        config.add_attribute('Position', 'x', 42)
        config.add_attribute('Position', 'y', 27)
        other_config = EntityConfiguration()
        config.add_attribute('Position', 'x', 34)
        config.add_component('Renderable')
        config.update(other_config)
        assert config.get_attributes('Renderable') == {}
        assert config.get_attributes('Position') == {'x': 34, 'y': 27}
