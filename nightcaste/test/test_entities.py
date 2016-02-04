import pytest
from nightcaste.entities import EntityManager
from nightcaste.entities import EntityConfiguration
from nightcaste.entities import ComponentManager
import nightcaste.components as components


@pytest.fixture
def component_manager():
    return ComponentManager()


@pytest.fixture
def simple_configuration():
    config = EntityConfiguration()
    config.add_attribute('Position', 'x', 42)
    config.add_attribute('Position', 'y', 23)
    config.add_attribute('Renderable', 'character', '@')
    return config


class TestEntityManager:

    def test_create_entity(self):
        em = EntityManager()
        entity1 = em.create_entity()
        entity2 = em.create_entity()

        assert entity1 == 0
        assert entity2 == 1

    def test_get_other_components_for_entites(self, simple_configuration):
        em = EntityManager()
        entity = em.create_entity_from_configuration(simple_configuration)
        positions = em.get_all_of_type("Position")
        renderables = em.get_other_components_for_entities(positions,
                                                           "Renderable")
        assert renderables[entity].character == "@"


class TestComponentManager:

    def test_add_component(self, component_manager):
        """Tests if components are added to the manager correctly"""
        id = 1
        component = components.Component()
        component_manager.add_component(id, component)
        assert 'Component' in component_manager.components
        assert 1 in component_manager.components['Component']
        assert component_manager.components['Component'][1] == component

    def test_add_components_by_configuration(self, component_manager):
        """Tests if the Component Manager can create components by
        configuration"""
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
        """Tests retrieving a component"""
        component = components.Component()
        component_manager.add_component(3, component)
        assert component_manager.get_component(3, component.type()) == component


class TestEntityConfiguration:

    def test_add_configuration(self):
        config = EntityConfiguration()
        config.add_attribute('Position', 'x', 42)
        config.add_attribute('Position', 'y', 27)

        assert config.components == {'Position': {'x': 42, 'y': 27}}
