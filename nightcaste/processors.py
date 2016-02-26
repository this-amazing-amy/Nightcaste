"""The module contains the event processors. An event processor must register
itself in the EventManager in order to retrieve the events to process"""
import game
from mapcreation import MapManager
import input
import logging
import utils

logger = logging.getLogger('processors')


class SystemManager:
    """Creates, configures and manages all GameSystems.

    Args:
        event_manager(EventManager): The event manager will be pass to all new
            systems.
        entity_manager (EntityManager): The entity manager will be passed to all
            systems.
        config (dict): (Optitonally) Create new systems from config.

    """

    def __init__(self, event_manager, entity_manager, config=None):
        self.systems = []
        self.event_manager = event_manager
        self.entity_manager = entity_manager
        if config is not None:
            self.configure(config)

    def configure(self, config):
        """Configure systems based on the given config.

        Args:
            config (dict):
                {
                    'systems': [{
                        'impl': 'systemClass',
                        'config': {systemparam: args}
                    }]
                }
        """
        if 'systems' in config:
            for system_config in config['systems']:
                self.add_system_by_config(system_config)

    def add_system(self, system):
        """Adds a system and calls its register function"""
        self.systems.append(system)
        # TODO rename to more general intialize
        system.register()

    def add_system_by_config(self, system_config):
        """Create and initialize a new system. The system has to be class in the
        module processors."""
        impl = system_config['impl']
        system_class = utils.class_for_name(impl[0], impl[1])
        system = system_class(self.event_manager, self.entity_manager)
        if 'config' in system_config:
            system.configure(system_config['config'])
        self.add_system(system)

    def update(self, round, delta_time):
        """Calls update on all systems."""
        for system in self.systems:
            system.update(round, delta_time)


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

    def configure(self, config):
        """Configure a special system parameters from a configuration or json
        structure."""
        pass

    def handle_event(self, event, round):
        """Base method which does not do anything which useful for testing.

            Args:
                event: The event to process.
                round: The current round and the game

        """
        pass

    def update(self, round, delta_time):
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
        return None


class MenuInputProcessor(InputProcessor):

    def _is_responsible_for(self, view_name):
        return view_name == 'menu'

    def _map_key_to_action(self, keycode):
        if keycode == input.K_ENTER:
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

        position = self.entity_manager.get(event.data['entity'], 'Position')

        if event.data.get("absolute", 0) == 1:
            target_x = event.data['dx']
            target_y = event.data['dy']
        else:
            target_x = position.x + event.data['dx']
            target_y = position.y + event.data['dy']

        collision = self.collision_manager.check(
            self.entity_manager.current_map,
            target_x, target_y)

        if (collision is None):
            # TODO: Change Movement behaviour, when sprites are done
            position.x_old = position.x
            position.y_old = position.y
            position.x = target_x
            position.y = target_y
            logger.debug('Move Entity %s to position %s,%s.',
                         event.data['entity'], target_x, target_y)
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
        # TODO let the event manager throw the event
        self.event_manager.throw(
            'EntityCreated', {
                'entity': self.entity_manager.player})
        self.event_manager.throw(
            'MapChange', {
                'name': 'world', 'level': 0, 'type': 'world'})


class MapChangeProcessor(EventProcessor):
    """Listens on MapChange Events and uses chnages or generates the maps
    accordingly."""

    def register(self):
        self._register('MapChange')

    def unregister(self):
        self._unregister('MapChange')

    def __init__(self, event_manager, entity_manager):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.map_manager = MapManager(entity_manager)

    def handle_event(self, event, round):
        if event.data["level"] is None:
            event.data["level"] = 0
        logger.debug(
            'Changing to Map %s - %d',
            event.data["name"],
            event.data["level"])
        new_map = self.map_manager.get_map(event.data['name'],
                                           event.data['level'],
                                           event.data.get("type", "dungeon"))
        entry_point = self.entity_manager.get(new_map, 'Map').entry
        self.event_manager.throw('MoveAction',
                                 {'entity': self.entity_manager.player,
                                  'dx': entry_point[0], 'dy': entry_point[1],
                                  'absolute': 1})
        self.change_map(new_map)

    def change_map(self, new_map):
        """Changes the current map with the specified map."""
        if self.entity_manager.current_map is not None:
            new_mc = self.entity_manager.get(new_map, 'Map')
            cur_mc = self.entity_manager.get(
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
        # TODO: Implement Sprite Collision, when Sprites are done
        if self.dummy:
            return None
        map = self.entity_manager.get(map, "Map").tiles
        target = self.entity_manager.get(map[x][y], component)
        if target is not None and target.active:
            # TODO: Throw better collision event
            self.event_manager.throw("EntitiesCollided", {"entities": target})
            return target
        return None


class SpriteProcessor(EventProcessor):

    def __init__(self, event_manager, entity_manager, sprite_manager):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.sprite_manager = sprite_manager

    def register(self):
        self._register('EntityCreated')
        self._register('EntityMoved')

    def unregister(self):
        self._unregister('EntityCreated')
        self._unregister('EntityMoved')

    def handle_event(self, event, round):
        entity = event.data['entity']
        sprite = self.entity_manager.get(entity, 'Sprite')
        if sprite is not None:
            if event.identifier == 'EntityMoved':
                logger.debug('Set sprite dirty %s', sprite)
                sprite.dirty = 1
            else:
                self.sprite_manager.initialize_sprite(sprite)


class TurnProcessor(EventProcessor):
    """Emulates the turns for turn based games be modifying the game status. The
    different component behaviours can react to the game state and performe
    actions only when they are allowed.

    TODO:
        This logic treats the player is special entity which determines the
        round logic. A better approach would be to let the behaviours schedule
        exactly one action in the COLLECT phase by implementing a logic in the
        BehaviourManager which checks if the behaviour has scheduled an action.
        If true, the the update function won't be called again until the next
        round. This way you could also collect input in multiplayer and start
        the round if all input is received."""

    def __init__(self, event_manager, entity_manager):
        EventProcessor.__init__(self, event_manager, entity_manager)
        # TODO Priority Queue?
        self.turn_events = []
        self.min_turn_time = 0.2
        self.current_turn_time = 0.0

    def configure(self, config):
        self.min_turn_time = config['min_turn_time']

    def register(self):
        self._register("MoveAction_TURN")
        self._register("UseEntityAction_TURN")

    def handle_event(self, event, round):
        self.turn_events.append(event)
        if game.status == game.G_ROUND_WAITING_INPUT:
            game.status = game.G_ROUND_INPUT_RECEIVED

    def update(self, round, delta_time):
        self.current_turn_time += delta_time
        if game.status == game.G_ROUND_INPUT_RECEIVED:
            game.status = game.G_ROUND_COLLECT_TURNS
        elif game.status == game.G_ROUND_COLLECT_TURNS:
            game.status = game.G_ROUND_IN_PROGRESS
            self.current_turn_time = 0
            # order by speed here

        # Throw a scheduled action on each update
        if game.status == game.G_ROUND_IN_PROGRESS:
            if len(self.turn_events) > 0:
                self._next_turn()
            elif (self.current_turn_time >= self.min_turn_time):
                game.status = game.G_ROUND_WAITING_INPUT
                game.round += 1

    def _next_turn(self):
        next_turn = self.turn_events.pop(0)
        next_turn.identifier = next_turn.identifier.rstrip('_TURN')
        self.event_manager.forward(next_turn)


class UseEntityProcessor(EventProcessor):
    """ Listens for UseEntity Events, determines Target Entity and throws its
    Use-Event """

    def register(self):
        self._register("UseEntityAction")

    def unregister(self):
        self._unregister("UseEntityAction")

    def handle_event(self, event, round):
        user = self.entity_manager.get(event.data['user'], 'Position')
        target = (user.x + event.data['direction'][0],
                  user.y + event.data['direction'][1])
        entity = self.entity_manager.get_current_map()[target[0]][target[1]]
        useable = self.entity_manager.get(entity, 'Useable')
        if (useable is not None):
            self.event_manager.throw(useable.useEvent, {'usedEntity': entity})


class TransitionProcessor(EventProcessor):
    """ Converts an Event into MapChange Events with the entity's MapTransition
    Component """

    def register(self):
        self._register("MapTransition")

    def unregister(self):
        self._unregister("MapTransition")

    def handle_event(self, event, round):
        target = self.entity_manager.get(
            event.data['usedEntity'], 'MapTransition')
        self.event_manager.throw("MapChange", {"name": target.target_map,
                                               "level": target.target_level})


class ViewProcessor(EventProcessor):
    """Listen on events which requires the view to react in some way. Therefore,
    the view has to provide methods to change its state."""

    def __init__(self, event_manager, entity_manager, window):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.window = window

    def register(self):
        self._register('MapChange')
        self._register('MenuOpen')
        self._register('EntityMoved')

    def unregister(self):
        self._unregister('MapChange')
        self._unregister('MenuOpen')
        self._unregister('EntityMoved')

    def handle_event(self, event, round):
        player = self.entity_manager.player
        if event.identifier == 'EntityMoved' and event.data[
                'entity'] == player:
            self.window.update_view('game')
        elif event.identifier == 'MapChange':
            if self.window.show('game'):
                # TODO let view_controller throw the event?
                self.event_manager.throw(
                    'ViewChanged', {'active_view': 'game'})
        elif event.identifier == 'MenuOpen':
            if self.window.show('main_menu'):
                self.event_manager.throw(
                    'ViewChanged', {'active_view': 'menu'})
