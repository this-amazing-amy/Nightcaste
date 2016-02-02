from nightcaste.model import EntityManager
from nightcaste.model import EntityConfiguration


class TestEntityManager:

    def test_create_entity(self):
        em = EntityManager()
        entity1 = em.create_entity()
        entity2 = em.create_entity()

        assert entity1 == 0
        assert entity2 == 1


class TestEntityConfiguration:

    def test_add_configuration(self):
        config = EntityConfiguration()
        config.add_attribute('Position', 'x', 42)
        config.add_attribute('Position', 'y', 27)

        assert config.components == {'Position': {'x': 42, 'y': 27}}
