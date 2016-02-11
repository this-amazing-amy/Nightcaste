"""The module contains the event processors. An event processor must register
itself in the EventManager in order to retrieve the events to process"""
from mapcreation import MapGenerator
from events import MapChange
from events import MoveAction
from events import WorldEnter
from events import EntitiesCollided
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

    def __str__(self):
        return self.__class__.__name__


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

    def __init__(self, event_manager, entity_manager, no_collision=False):
        self.event_manager = event_manager
        self.entity_manager = entity_manager
        self.collision_manager = CollisionManager(self.entity_manager,
                                                  self.event_manager,
                                                  no_collision)

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

        position = self.entity_manager.get_entity_component(
            event.entity, 'Position')

        target_x = position.x + event.dx
        target_y = position.y + event.dy

        collision = self.collision_manager.check(
            self.entity_manager.current_map,
            target_x, target_y)

        if (collision is None):
            map = self.entity_manager.get_current_map()
            map[position.x][position.y] = [entity for entity in map[
                position.x][position.y] if entity != event.entity]
            map[target_x][target_y].append(event.entity)
            position.x = target_x
            position.y = target_y
            logger.debug('Move Entity %s to position %s,%s. There are now: %s',
                         event.entity, target_x, target_y,
                         map[target_x][target_y])


class WorldInitializer(EventProcessor):
    """Registers to WorldEnteredEvent and performs necessary world
    initialization."""

    def register(self):
        self._register('WorldEnter')

    def unregister(self):
        self._unregister('WorldEnter')

    def handle_event(self, event, round):
        self.entity_manager.player = self.entity_manager.new_from_blueprint(
            'game.player')

        # TODISCUSS: Do we need to save the Listeners?
        MapChangeProcessor(self.event_manager, self.entity_manager).register()
        MovementProcessor(self.event_manager, self.entity_manager).register()

        self.event_manager.enqueue_event(MapChange('World', 0))


class MapChangeProcessor(EventProcessor):
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
        new_map = self.map_generator.generate_map(event.map_name, event.level)
        # place player at the dungeon entry
        self.event_manager.enqueue_event(
            MoveAction(self.entity_manager.player, 20, 10))
        self.change_map(new_map)

    def change_map(self, new_map):
        """Changes the current map with the specified map."""
        if self.entity_manager.current_map is not None:
            new_mc = self.entity_manager.get_entity_component(new_map, 'Map')
            cur_mc = self.entity_manager.get_entity_component(
                self.entity_manager.current_map, 'Map')
            new_mc.parent = self.entity_manager.current_map
            cur_mc.add_child(new_map)
        self.entity_manager.current_map = new_map
        # TODO: Throw event so the mobs can be placed


class CollisionManager():

    def __init__(self, entity_manager, event_manager, dummy=False):
        self.entity_manager = entity_manager
        self.event_manager = event_manager
        self.dummy = dummy

    def check(self, map, x, y, component="Colliding"):
        """ Checks for collisions on map-(x,y) and returns all entites
        colliding on this spot.

        Args:
            map (int): Entity_id of the map to test on
            x (int): x position to check
            y (int): y position to check
            component (str): Component identifier which determines collision
            e.g. to test for other collisions (fov)
        """
        if self.dummy:
            return None
        map = self.entity_manager.get_entity_component(map, "Map").tiles
        collidings = {entity: self.entity_manager.get_entity_component(
            entity,
            component)
            for entity in map[x][y]}
        active = [e for e, v in collidings.iteritems() if v.active]
        if (len(active) > 0):
            # TODO: Throw better collision event
            self.event_manager.enqueue_event(EntitiesCollided(active))
            return active
        return None
