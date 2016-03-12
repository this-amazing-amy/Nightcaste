"""The module contains the event processors. An event processor must register
itself in the EventManager in order to retrieve the events to process"""
import game
from mapcreation import MapManager
import input
import logging
import utils
from sound import SoundBank


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


class EventProcessor(object):
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

    def update(self, round, delta_time):
        pass

    def register(self):
        pass

    def unregister(self):
        pass

    def _register(self, event_type, process_function):
        self.event_manager.register_listener(event_type, process_function)

    def _unregister(self, event_type, process_function):
        self.event_manager.remove_listener(event_type, process_function)

    def __str__(self):
        return self.__class__.__name__


class InputProcessor(EventProcessor):

    logger = logging.getLogger('processors.InputProcessor')

    def register(self):
        self._register('ViewChanged', self.on_view_changed)

    def unregister(self):
        self._unregister('ViewChanged', self.on_view_changed)

    def on_view_changed(self, event):
        if self._is_responsible_for(event.data["active_view"]):
            self._register('KeyPressed', self.on_key_pressed)
        else:
            self._unregister('KeyPressed', self.on_key_pressed)

    def on_key_pressed(self, event):
        action = self._map_key_to_action(event.data["keycode"])
        self.logger.debug('Mapped key %s to %s', event.data["keycode"], action)
        if action is not None:
            self.event_manager.throw(action[0], action[1])


class GameInputProcessor(InputProcessor):
    """Handle all key inputs if the player is in the world and not showing a
    menu."""

    def _is_responsible_for(self, view_name):
        return view_name == 'game_view'

    def _map_key_to_action(self, keycode):
        return None


class MenuInputProcessor(InputProcessor):

    def _is_responsible_for(self, view_name):
        return view_name == 'main_menu'

    def _map_key_to_action(self, keycode):
        if keycode == input.K_ENTER:
            return ("WorldEnter", None)
        return None


class MovementProcessor(EventProcessor):

    logger = logging.getLogger('processors.MovementProcessor')

    def __init__(self, event_manager, entity_manager, no_collision=False):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.collision_manager = CollisionManager(entity_manager,
                                                  event_manager,
                                                  no_collision)

    def register(self):
        self._register('MoveAction', self.on_move)

    def unregister(self):
        self._unregister('MoveAction', self.on_move)

    def on_move(self, event):
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
            position.x = target_x
            position.y = target_y
            self.logger.debug(
                'Move Entity %s to position %s,%s.',
                event.data['entity'],
                target_x,
                target_y)
            self.event_manager.throw('EntityMoved', {'entity': event.data[
                'entity'], 'x': target_x, 'y': target_y})


class WorldInitializer(EventProcessor):
    """Registers to WorldEnteredEvent and performs necessary world
    initialization."""

    def register(self):
        self._register('WorldEnter', self.on_world_enter)

    def unregister(self):
        self._unregister('WorldEnter', self.on_world_enter)

    def configure(self, config):
        self.start_time = config.get('start_time', 0)

    def on_world_enter(self, event):
        game.time = self.start_time
        self.entity_manager.player = self.entity_manager.new_from_blueprint(
            'game.player')
        # TODO let the entity manager throw the event
        self.event_manager.throw(
            'EntityCreated', {
                'entity': self.entity_manager.player})
        self.event_manager.throw(
            'MapChange', {
                'name': 'world', 'level': 0, 'type': 'world'})


class MapChangeProcessor(EventProcessor):
    """Listens on MapChange Events and uses chnages or generates the maps
    accordingly."""
    logger = logging.getLogger('processors.MapChangeProcessor')

    def register(self):
        self._register('MapChange', self.on_map_change)

    def unregister(self):
        self._unregister('MapChange', self.on_map_change)

    def __init__(self, event_manager, entity_manager):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.map_manager = MapManager(entity_manager)

    def on_map_change(self, event):
        if event.data["level"] is None:
            event.data["level"] = 0
        self.logger.debug(
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
    """Initializes sprites of created entites with sprite components. Detects
    moved Sprites and updates their dirty flag."""
    logger = logging.getLogger('processors.SpriteProcessor')

    def __init__(self, event_manager, entity_manager, sprite_manager):
        EventProcessor.__init__(self, event_manager, entity_manager)
        self.sprite_manager = sprite_manager

    def register(self):
        self._register('EntityCreated', self.on_entity_created)
        self._register('EntityMoved', self.on_entity_moved)

    def unregister(self):
        self._unregister('EntityCreated', self.on_entity_created)
        self._unregister('EntityMoved', self.on_entity_moved)

    def on_entity_created(self, event):
        entity = event.data['entity']
        sprite = self.entity_manager.get(entity, 'Sprite')
        if sprite is not None:
            self.sprite_manager.initialize_sprite(sprite)

    def on_entity_moved(self, event):
        entity = event.data['entity']
        sprite = self.entity_manager.get(entity, 'Sprite')
        if sprite is not None:
            self.logger.debug('Set sprite dirty %s', sprite)
            sprite.dirty = 1

    def update(self, round, delta_time):
        for entity, sprite in self.entity_manager.get_all(
                'Sprite').iteritems():
            sprite.update(round, delta_time)


class UseEntityProcessor(EventProcessor):
    """ Listens for UseEntity Events, determines Target Entity and throws its
    Use-Event """

    def register(self):
        self._register("UseEntityAction", self.on_use_entity)

    def unregister(self):
        self._unregister("UseEntityAction", self.on_use_entity)

    def on_use_entity(self, event):
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
        self._register("MapTransition", self.on_map_transition)

    def unregister(self):
        self._unregister("MapTransition", self.on_map_transition)

    def on_map_transition(self, event):
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
        self._register('MapChange', self.on_map_change)
        self._register('MenuOpen', self.on_menu_open)
        self._register('EntityMoved', self.on_entity_moved)

    def unregister(self):
        self._unregister('MapChange', self.on_map_change)
        self._unregister('MenuOpen', self.on_menu_open)
        self._unregister('EntityMoved', self.on_entity_moved)

    def on_map_change(self, event):
        # TODO: make view active on world enter and handle map updating with a
        # simple map.dirty flag
        if self.window.show('game_view'):
            # TODO let view_controller throw the event?
            self.event_manager.throw(
                'ViewChanged', {'active_view': 'game_view'})

    def on_menu_open(self, event):
        if self.window.show('main_menu'):
            self.event_manager.throw(
                'ViewChanged', {'active_view': 'main_menu'})

    def on_entity_moved(self, event):
        # Update the game view (calculates viewport) if the player has moved
        if event.data['entity'] == self.entity_manager.player:
            self.window.update_view('game_view')


class SoundSystem(EventProcessor):

    logger = logging.getLogger('processors.SoundSystem')

    def configure(self, config):
        self.sound_bank = SoundBank(config['sound_path'])

    def play(self, key):
        sound = self.sound_bank.get(key)
        if sound is not None:
            sound.play()
        else:
            self.logger.error('Sound %s does not exits in sound bank.', key)


class PocSoundSystem(SoundSystem):

    def register(self):
        self._register('MenuOpen', self.on_menu_open)

    def on_menu_open(self, event):
        self.play('smb_stage_clear.wav')


class GameTimeSystem(EventProcessor):

    def __init__(self, event_manager, entity_manager):
        super(GameTimeSystem, self).__init__(event_manager, entity_manager)
        self.time_multi = 1.0

    def configure(self, config):
        self.time_multi = config['time_multi']

    def update(self, round, delta_time):
        if game.status != game.G_PAUSED:
            game.time += delta_time * self.time_multi
