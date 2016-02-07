"""The module contains the event processors. An event processor must register
itself in the EventManager in order to retrieve the events to process"""
from entities import EntityConfiguration
from entities import MapGenerator
from events import MapChange
from events import MoveAction
from events import WorldEnter
import tcod as libtcod
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

    def register(self):
        pass

    def unregister(self):
        pass

    def _register(self, event_type):
        self.event_manager.register_listener(event_type, self)

    def _unregister(self, event_type):
        self.event_manager.remove_listener(event_type, self)


class InputProcessor(EventProcessor):

    def register(self):
        self._register('KeyPressed')

    def unregister(self):
        self._unregister('KeyPressed')

    def handle_event(self, event, round):
        action = self._map_key_to_action(event.code)
        logger.debug('Mapped key %s to action %s', event.code, action)
        if action is not None:
            self.event_manager.enqueue_event(action)


class GameInputProcessor(InputProcessor):
    """Handle all key inputs if the player is in the world and not showing a
    menu."""

    def _map_key_to_action(self, keycode):
        if keycode == libtcod.KEY_UP:
            return MoveAction(self.entity_manager.player, 0, -1)
        elif keycode == libtcod.KEY_DOWN:
            return MoveAction(self.entity_manager.player, 0, 1)
        elif keycode == libtcod.KEY_LEFT:
            return MoveAction(self.entity_manager.player, -1, 0)
        elif keycode == libtcod.KEY_RIGHT:
            return MoveAction(self.entity_manager.player, 1, 0)
        return None


class MenuInputProcessor(InputProcessor):

    def _map_key_to_action(self, keycode):
        if keycode == libtcod.KEY_ENTER:
            # TODO Who is resposible for adding and removing the key listeners
            self.unregister()
            GameInputProcessor(
                self.event_manager,
                self.entity_manager).register()
            return WorldEnter()
        return None


class MovementProcessor(EventProcessor):

    def register(self):
        self._register('MoveAction')

    def unregister(self):
        self._unregister('MoveAction')

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

    def register(self):
        self._register('WorldEnter')

    def unregister(self):
        self._unregister('WorldEnter')

    def handle_event(self, event, round):
        # Creating Player from Configuration
        # TODO: Make a Player Blueprint
        player_config = EntityConfiguration()
        player_config.add_attribute('Position', 'x', 0)
        player_config.add_attribute('Position', 'y', 0)
        player_config.add_attribute('Renderable', 'character', "@")
        player_config.add_attribute('Renderable', 'z_index', 99)
        player_config.add_attribute('Color', 'r', 239)
        player_config.add_attribute('Color', 'g', 228)
        player_config.add_attribute('Color', 'b', 176)
        self.entity_manager.player = self.entity_manager.create_entity_from_configuration(
            player_config)

        # TODISCUSS: Do we need to save the Listeners?
        MapProcessor(self.event_manager, self.entity_manager).register()
        MovementProcessor(self.event_manager, self.entity_manager).register()

        self.event_manager.enqueue_event(MapChange('World', 0))


class MapProcessor(EventProcessor):
    """Listens on MapChange Events and uses chnages or generates the maps
    accordingly."""

    def register(self):
        self._register('MapChange')

    def unregister(self):
        self._unregister('MapChange')

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
