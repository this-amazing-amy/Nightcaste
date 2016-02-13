"""The module contains the event processors. An event processor must register
itself in the EventManager in order to retrieve the events to process"""
from mapcreation import MapGenerator
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
        self._register('ViewChanged')

    def unregister(self):
        self._unregister('ViewChanged')

    def handle_event(self, event, round):
        if event.identifier == 'KeyPressed':
            action = self._map_key_to_action(event.data["keycode"])
            logger.debug('Mapped key %s to action %s', event.data["keycode"],
                         action)
            if action is not None:
                self.event_manager.throw(action[0], action[1])
        else:
            if self._is_responsible_for(event.data["active_view"]):
                self._register('KeyPressed')
            else:
                self._unregister('KeyPressed')


class GameInputProcessor(InputProcessor):
    """Handle all key inputs if the player is in the world and not showing a
    menu."""

    def _is_responsible_for(self, view_name):
        return view_name == 'game'

    def _map_key_to_action(self, keycode):
        if keycode == libtcod.KEY_UP:
            return ("MoveAction", {'entity': self.entity_manager.player,
                                   'dx': 0, 'dy': -1})
        elif keycode == libtcod.KEY_DOWN:
            return ("MoveAction", {'entity': self.entity_manager.player,
                                   'dx': 0, 'dy': 1})
        elif keycode == libtcod.KEY_LEFT:
            return ("MoveAction", {'entity': self.entity_manager.player,
                                   'dx': -1, 'dy': 0})
        elif keycode == libtcod.KEY_RIGHT:
            return ("MoveAction", {'entity': self.entity_manager.player,
                                   'dx': 1, 'dy': 0})
        elif keycode == libtcod.KEY_ENTER:
            # TODO: Needs Simultaneous/Consecutive Keypresses to use blocking
            # entities
            return ("UseEntityAction",
                    {'entity': self.entity_manager.player,
                     'dx': 0, 'dy': 0})
        return None


class MenuInputProcessor(InputProcessor):

    def _is_responsible_for(self, view_name):
        return view_name == 'menu'

    def _map_key_to_action(self, keycode):
        if keycode == libtcod.KEY_ENTER:
            return ("WorldEnter", None)
        return None


class MovementProcessor(EventProcessor):

    def __init__(self, event_manager, entity_manager, no_collision=False):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.collision_manager = CollisionManager(entity_manager,
                                                  event_manager,
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
            event.data['entity'], 'Position')

        target_x = position.x + event.data['dx']
        target_y = position.y + event.data['dy']

        collision = self.collision_manager.check(
            self.entity_manager.current_map,
            target_x, target_y)

        if (collision is None):
            map = self.entity_manager.get_current_map()
            try:
                map[position.x][position.y].remove(event.data['entity'])
            except ValueError:
                pass
            map[target_x][target_y].append(event.data['entity'])
            position.x = target_x
            position.y = target_y
            logger.debug('Move Entity %s to position %s,%s. There are now: %s',
                         event.data['entity'], target_x, target_y,
                         map[target_x][target_y])
            self.event_manager.throw("EntityMoved",
                                     {'entity': event.data['entity'],
                                      'x': target_x, 'y': target_y})


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
        UseEntityProcessor(self.event_manager, self.entity_manager).register()

        self.event_manager.throw('MapChange', {'map': 'World', 'level': 0})


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
            event.data["map"],
            event.data["level"])
        new_map = self.map_generator.generate_map(
            event.data['map'], event.data['level'])
        # place player at the dungeon entry
        self.event_manager.throw('MoveAction',
                                 {'entity': self.entity_manager.player,
                                  'dx': 20, 'dy': 10})
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
        active = [e for e, v in collidings.iteritems()
                  if v is not None and v.active]
        if (len(active) > 0):
            # TODO: Throw better collision event
            self.event_manager.throw("EntitiesCollided", {"entities": active})
            return active
        return None


class UseEntityProcessor(EventProcessor):
    """ Listens for UseEntity Events, determines Target Entity and throws its
    Use-Event """

    def register(self):
        self._register("UseEntityAction")

    def unregister(self):
        self._unregister("UseEntityAction")

    def handle_event(self, event, round):
        user = self.entity_manager.get_entity_component(event.data['user'],
                                                        "Position")
        target = (user.x + event.data['direction'][0],
                  user.y + event.data['direction'][1])
        entities = self.entity_manager.get_current_map()[target[0]][target[1]]
        useables = {x: self.entity_manager.get_entity_component(x, "Useable")
                    for x in entities}
        for i in useables:
            if (useables[i] is not None):
                self.event_manager.throw(useables[i].useEvent,
                                         {'usedEntity': i})


class ViewProcessor(EventProcessor):
    """Listen on events which requires the view to react in some way. Therefore,
    the view has to provide methods to change its state."""

    def __init__(self, event_manager, entity_manager, view_controller):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.view_controller = view_controller

    def register(self):
        self._register('WorldEnter')
        self._register('MenuOpen')
        self._register('EntityMoved')

    def unregister(self):
        self._unregister('WorldEnter')
        self._unregister('MenuOpen')
        self._unregister('EntityMoved')

    def handle_event(self, event, round):
        player = self.entity_manager.player
        if event.identifier == 'EntityMoved' and event.data['entity'] == player:
            self.view_controller.update_view('game')
        elif event.identifier == 'WorldEnter':
            if self.view_controller.show('game'):
                # TODO let view_controller throw the event?
                self.event_manager.throw(
                    'ViewChanged', {'active_view': 'game'})
        elif event.identifier == 'MenuOpen':
            if self.view_controller.show('menu'):
                self.event_manager.throw(
                    'ViewChanged', {'active_view': 'menu'})
