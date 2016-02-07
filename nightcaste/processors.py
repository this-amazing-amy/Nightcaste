"""The module contains the event processors. An event processor must register
itself in the EventManager in order to retrieve the events to process"""
from entities import EntityConfiguration
from entities import MapGenerator
from events import MapChange
from events import MoveAction
import logging

logger = logging.getLogger('processors')


class EventProcessor:
    """Base class for all processors.

        Args:
            event_manager (EventManager): The event manager for enqueuing new
                events.
            entity_manager (EntityManager): The entity manager for creating,
                destroying entities and access their properties

    """

    def __init__(self, event_manager, entity_manager):
        self.event_manager = event_manager
        self.entity_manager = entity_manager

    def handle_event(self, event, round):
        """Base method which does not do anything which useful for testing.

            Args:
                event: The event to process.
                round: The current round and the game

        """
        pass


class MovementProcessor(EventProcessor):

    def handle_event(self, event, round):
        """Checks for collision and moves the entity the specified amount. If a
        collision is detected an appropriate event will be created.

            Args:
                event: The event to process.
                round: The current round and the game

        """

        # TODO: CollisionManager.check and throw an appropriate event

        position = self.entity_manager.get_entity_component(
            event.entity, 'Position')
        # TODO: Save absolute target position and go only evnt.steps if target
        # not reached, reraise event (needs path finding logic)
        position.x += event.dx
        position.y += event.dy
        logger.debug('Move Entity %s to position %s', event.entity, position)


class WorldInitializer(EventProcessor):
    """Registers to WorldEnteredEvent and performs necessary world
    initialization."""

    def __init__(self, event_manager, entity_manager):
        EventProcessor.__init__(self, event_manager, entity_manager)
        event_manager.register_listener('WorldEnter', self)

    def handle_event(self, event, round):
        # Creating Player from Configuration
        # TODO: Make a Player Blueprint
        player_config = EntityConfiguration()
        player_config.add_attribute("Position", "x", 0)
        player_config.add_attribute("Position", "y", 0)
        player_config.add_attribute("Renderable", "character", "@")
        player_config.add_attribute("Renderable", "z_index", 99)
        player_config.add_attribute("Color", "r", 239)
        player_config.add_attribute("Color", "g", 228)
        player_config.add_attribute("Color", "b", 176)
        self.entity_manager.player = self.entity_manager.create_entity_from_configuration(
            player_config)

        # TODISCUSS: Do we need to save the Listeners?
        # TODO Let processors register themselves
        self.event_manager.register_listener(
            "MapChange", MapProcessor(
                self.event_manager, self.entity_manager))
        self.event_manager.register_listener(
            "MoveAction", MovementProcessor(
                self.event_manager, self.entity_manager))

        self.event_manager.enqueue_event(MapChange('world', 0))


class MapProcessor(EventProcessor):
    """Listens on MapChange Events and uses chnages or generates the maps
    accordingly."""

    def __init__(self, event_manager, entity_manager):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.map_generator = MapGenerator(entity_manager)

    def handle_event(self, event, round):
        logger.debug(
            'Generating Map %s on level %d',
            event.map_name,
            event.level)
        self.map_generator.generate_map(event.map_name, event.level)
        # place player at the dungeon entry
        self.event_manager.enqueue_event(
            MoveAction(self.entity_manager.player, 20, 10))
