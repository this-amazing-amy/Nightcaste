"""The Rendering Framework, wrapping around the libtcod
console."""
from nightcaste import __version__
from nightcaste.components import Color
from nightcaste.processors import SpriteProcessor
from nightcaste.processors import ViewProcessor
from os import path
import game
import json
import logging
import pygame
import tcod as libtcod

logger = logging.getLogger('renderer')
TILESET_DIR = path.abspath(
    path.join(
        path.dirname(__file__),
        '..',
        'config',
        'tilesets'))
SPRITE_DIR = path.abspath(
    path.join(
        path.dirname(__file__),
        '..',
        'config',
        'sprites'))


class PygameRenderer:

    def __init__(self, console, title, width=80, height=55):
        self.console = console
        self.color_cache = {}
        self.dirty_rects = []

        tileset_file = open(path.join(TILESET_DIR, 'ascii.json'))
        tiles_config = json.load(tileset_file)
        # Only configures the tile size the tileset image cannot be loaded yet
        self.tileset = TileSet(tiles_config)
        screen_width = width * self.tileset.tile_width
        screen_height = height * self.tileset.tile_height
        self.screen = pygame.display.set_mode([screen_width, screen_height])
        self.surface = pygame.Surface((screen_width, screen_height))

        # We cannot load the image before the screen is initialized but we need
        # the tile size to calculate the screen size so here come the "real"
        # TileSet __init__ wich create the tiles map (will be changed "soon")
        self.tileset.configure_tiles(tiles_config)

    def clear(self):
        """Removes all content from the console"""
        pass

    def flush(self):
        """Flush the changes to screen."""
        self.screen.blit(self.surface, (0, 0))
        pygame.display.update(self.dirty_rects)
        self.dirty_rects = []

    def put_char(self, x, y, char, fore_color=None, back_color=None):
        tile = self.tileset.get_tile(char)
        self.surface.blit(
            tile,
            (x * self.tileset.tile_width,
             y * self.tileset.tile_height))

    def put_tile(self, x, y, tile_name):
        tile = self.tileset.get_tile(tile_name)
        rects = self.surface.blit(
            tile,
            (x * self.tileset.tile_width,
             y * self.tileset.tile_height))
        self.dirty_rects.append(rects)

    def fill_background(self, color, rect):
        rects = self.surface.fill(
            (color.r,
             color.g,
             color.b),
            pygame.Rect(
                rect[0] * self.tileset.tile_width,
                rect[1] * self.tileset.tile_height,
                rect[2] * self.tileset.tile_width,
                rect[3] * self.tileset.tile_height))
        self.dirty_rects.append(rects)

    def put_text(self, x, y, text, fcolor=None, bcolor=None):
        for text_index in range(0, len(text)):
            self.put_char(x + text_index, y, text[text_index], fcolor, bcolor)

    def put_sprite(self, sprite):
        if sprite.visible:
            sprite.rect.x *= self.tileset.tile_width
            sprite.rect.y *= self.tileset.tile_height
            rects = self.surface.blit(sprite.image, sprite.rect)
            self.dirty_rects.append(rects)
            # TODO let handle pygame the dirty flags by using sprite groups
            sprite.dirty = 0


class TileSet:

    def __init__(self, config):
        self.tiles = {}
        general_config = config['general']
        self.tile_width = general_config['tile_width']
        self.tile_height = general_config['tile_height']

    def configure_tiles(self, config):
        general_config = config['general']
        filename = path.join(TILESET_DIR, general_config['filename'])
        tile_table = self._load_tile_table(filename)
        tile_definitions = config['tiles']
        for tile_def in tile_definitions:
            key = tile_def['key']
            tableposition = tile_def['position']
            tile = tile_table[tableposition[0]][tableposition[1]]
            self.add_tile(key, tile)

    def add_tile(self, key, tile):
        self.tiles.update({key: tile})

    def get_tile(self, key):
        return self.tiles[key]

    def _load_tile_table(self, filename):
        image = pygame.image.load(filename).convert()
        image_width, image_height = image.get_size()
        tile_table = []
        for tile_x in range(0, image_width / self.tile_width):
            line = []
            tile_table.append(line)
            for tile_y in range(0, image_height / self.tile_height):
                rect = (
                    tile_x * self.tile_width,
                    tile_y * self.tile_height,
                    self.tile_width,
                    self.tile_height)
                line.append(image.subsurface(rect))
        return tile_table


class SpriteManager:

    def __init__(self):
        self.images = {}

    def initialize_sprite(self, sprite):
        image = self.images.get(sprite.name)
        if image is None:
            image = self._load_image(sprite.name)
        sprite.image = image.copy()
        sprite.rect = image.get_rect()
        logger.debug('Sprite initialized %s', sprite)

    def _load_image(self, name):
        """Assume the name is a direct path to an image containing exactly the
        required sprite image.
        TODO: Support load_by_config which can load a complete sprite set from
        configuration like with a TileSet."""
        # TEST
        filename = path.join(TILESET_DIR, 'terminal.png')
        image = pygame.image.load(filename).convert_alpha()
        at = image.subsurface((32, 0, 8, 8))
        return at


class WindowManager:

    def __init__(self, event_manager, entity_manager):
        self.windows = []
        self.event_manager = event_manager
        self.entity_manager = entity_manager

    def create_empty_window(self, title, width, height):
        window = Window(len(self.windows), title, width,
                        height, self.event_manager, self.entity_manager)
        self.windows.append(window)
        return window

    def create_window_from_config(self, config):
        window = Window(len(self.windows) + 1,
                        config['title'],
                        config['width'],
                        config['height'],
                        self.event_manager,
                        self.entity_manager)
        self.windows.append(window)
        return window


class Window:
    """A window an which something can be rendered. Supports multiple views with
    content panes in them."""

    def __init__(self, number, title, width, height,
                 event_manager, entity_manager):
        self.event_manager = event_manager
        self.entity_manager = entity_manager
        self.view_controller = ViewController()
        self.sprite_manager = SpriteManager()
        self.renderer = PygameRenderer(number, title, width, height)
        ViewProcessor(
            event_manager,
            entity_manager,
            self.view_controller).register()
        SpriteProcessor(
            event_manager,
            entity_manager,
            self.sprite_manager).register()

    def add_view(self, name):
        return self.view_controller.add_view(name)

    def is_active(self):
        return True

    def put_char(self, x, y, char, fore_color, back_color):
        """Delegates the call to the renderer."""
        self.renderer.put_char(x, y, char, fore_color, back_color)

    def put_text(self, x, y, text, fore_color, back_color):
        """Delegates the call to the renderer."""
        self.renderer.put_text(x, y, text, fore_color, back_color)

    def put_sprite(self, sprite):
        """Delegates the call to renderer."""
        self.renderer.put_sprite(sprite)

    def put_tile(self, x, y, tile_name):
        """Delegates the call to the renderer."""
        self.renderer.put_tile(x, y, tile_name)

    def fill_background(self, color, rect):
        self.renderer.fill_background(color, rect)

    def render(self):
        self.renderer.clear()
        self.view_controller.render()
        self.renderer.flush()


class ViewController:

    def __init__(self):
        self._views = {}
        self._active_view = None

    def add_view(self, name):
        view = View()
        self._views.update({name: view})
        return view

    def get_view(self, name):
        return self._views.get(name)

    def update_view(self, name):
        view = self.get_view(name)
        if view is not None:
            view.update()

    def show(self, name):
        """Shows the specified view. This methods disables all other views."""
        view_changed = False
        for id, view in self._views.iteritems():
            if name == id and not view.active:
                view.active = True
                view_changed = True
                self._active_view = view
                view._initialize()
            else:
                view.active = False
        return view_changed

    def render(self):
        if self._active_view is not None:
            self._active_view.render()


class View:

    def __init__(self, active=False):
        self._panes = {}
        self.active = active

    def _initialize(self):
        for pane in sorted(self._panes.itervalues(), key=lambda v: v.z_index):
            pane.initialize()

    def add_pane(self, name, pane):
        # TODO refactor: create pane and let the view manage the panes (also
        # check for coliding panes, etc
        self._panes.update({name: pane})

    def update(self):
        """Calls update on all panes"""
        for pane in self._panes.itervalues():
            pane.update()

    def render(self):
        """Renders all panes."""
        for pane in sorted(self._panes.itervalues(), key=lambda v: v.z_index):
            pane.render()


class ContentPane(object):
    """Can be printed with colored text"""

    def __init__(self, window, absolute_x,
                 absolute_y, width, height, z_index=0):
        self.window = window
        self.pos_x = absolute_x
        self.pos_y = absolute_y
        self.width = width
        self.height = height
        self.z_index = z_index
        self.default_background = Color(0, 0, 0)
        self.default_foreground = Color(175, 175, 175)

    def initialize(self):
        logger.debug('initialize %s', self)
        self.print_background()

    def put_char(self, x, y, char, fore_color=None, back_color=None):
        self.print_background(back_color, rect=(x, y, 1, 1))
        self.window.put_char(
            self.pos_x + x,
            self.pos_y + y,
            char,
            self.default_foreground if fore_color is None else fore_color,
            self.default_background if back_color is None else back_color)

    def put_sprite(self, sprite):
        sprite.rect.x += self.pos_x
        sprite.rect.y += self.pos_y
        # As long as we use tansparant tiles for printing text we have to
        # print the background to overwrite existing chars
        self.window.put_sprite(sprite)

    def put_tile(self, x, y, tile_name):
        self.window.put_tile(
            self.pos_x + x,
            self.pos_y + y,
            tile_name)

    def put_text(self, x, y, text, fore_color=None, back_color=None):
        # As long as we use tansparant tiles for printing text we have to
        # print the background to overwrite existing chars
        self.print_background(back_color, rect=(x, y, len(text), 1))
        self.window.put_text(
            self.pos_x + x,
            self.pos_y + y,
            text,
            self.default_foreground if fore_color is None else fore_color,
            self.default_background if back_color is None else back_color)

    def print_background(self, color=None, rect=None):
        if color is None:
            color = self.default_background
        if rect is None:
            rect = (self.pos_x, self.pos_y, self.width, self.height)
        else:
            rect = (self.pos_x + rect[0],
                    self.pos_y + rect[1], rect[2], rect[3])

        self.window.fill_background(color, rect)

    def update(self):
        """Updates the internal state of the pane."""
        pass


class MapPane(ContentPane):
    """Renders every visible component, e.g the map with all its entities"""

    def __init__(self, window, absolute_x,
                 absolute_y, width, height, z_index=0):
        ContentPane.__init__(self, window, absolute_x,
                             absolute_y, width, height, z_index=0)
        self.viewport_x = 0
        self.viewport_y = 0
        self.viewport_dirty = True

    def initialize(self):
        super(MapPane, self).initialize()
        self.viewport_dirty = True

    def update(self):
        """Updates the view port"""
        self._update_view_port()

    def render(self):
        """Renders all entities with a visible renderable component and with a
        position in the current viewport."""
        if self.viewport_dirty:
            self._render_map()
            self.viewport_dirty = False
        self._render_sprites()

    def _render_map(self):
        em = self.window.entity_manager
        if em.current_map is not None:
            to_render = [x for y in em.get_current_map() for x in y]
            self._render_tiles(to_render)

    def _render_sprites(self):
        # TODO: Render SpriteGroups instead of individual sprites
        em = self.window.entity_manager
        positions = em.get_all('Position')
        sprites = em.get_all('Sprite')
        for entity, sprite in sorted(
                sprites.iteritems(), key=lambda k_v: k_v[1].z_index):
            self._render_sprite(entity, sprite, positions[entity])

    def _render_tiles(self, entities):
        """ Iterates through a list of entities and renders each """
        em = self.window.entity_manager
        tiles = {k: v for k, v in em.get_components_for_entities(
            entities, 'Tile').iteritems() if v.visible}
        positions = em.get_components_for_entities(entities, 'Position')
        colors = em.get_components_for_entities(entities, 'Color')
        for entity, tile in sorted(
                tiles.iteritems(), key=lambda k_v1: k_v1[1].z_index):
            self._render_tile(tile, positions[entity], colors[entity])

    def _render_tile(self, tile, position, color):
        """Check if the position of the given entity is in the viewport and
        render the entety to the window with the recalculated position in the
        pane.

        Args:
            entity (object): the entity which should be rendered.
            tile (Tile): The visible renderable component of the
                given entity.

        """
        if self._in_viewport(position):
            self.put_tile(
                position.x - self.viewport_x,
                position.y - self.viewport_y,
                tile.name)

    def _render_sprite(self, entity, sprite, position):
        # restore map tile at old position
        if sprite.dirty > 0:
            em = self.window.entity_manager
            old_tile_entity = em.get_current_map()[position.x_old][
                position.y_old]
            old_tile = em.get(old_tile_entity, 'Tile')
            self.put_tile(
                position.x_old - self.viewport_x,
                position.y_old - self.viewport_y,
                old_tile.name)
            # render sprite at new position
            sprite.rect.x = position.x - self.viewport_x
            sprite.rect.y = position.y - self.viewport_y
            self.put_sprite(sprite)

    def _update_view_port(self):
        """The viewport is the visble range of the map. The viewport is always
        centered on the player until it hits the edges of the map. The viewport
        is represented by a start point + width and high of the pane."""
        em = self.window.entity_manager
        map = em.get(em.current_map, 'Map')
        player_pos = em.get(em.player, 'Position')
        vp_x_old = self.viewport_x
        vp_y_old = self.viewport_y
        self.viewport_x = max(player_pos.x - int(self.width / 2), 0)
        self.viewport_y = max(player_pos.y - int(self.height / 2), 0)
        self.viewport_x += min(map.width() - (self.viewport_x + self.width), 0)
        self.viewport_y += min(map.height() -
                               (self.viewport_y + self.height), 0)
        if self.viewport_x != vp_x_old or self.viewport_y != vp_y_old:
            self.viewport_dirty = True

    def _in_viewport(self, position):
        """Checks if the given position is in the current viewport.

        Returns:
            viewport_start <= position < viewport_start + width

        """
        if self.viewport_x <= position.x < self.viewport_x + self.width:
            if self.viewport_y <= position.y < self.viewport_y + self.height:
                return True
        return False


class StatusPane(ContentPane):

    def render(self):
        self.put_text(0, 0, 'Health: 100')
        self.put_text(0, 1, 'Round: %s' % (game.round))


class MenuPane(ContentPane):

    def __init__(self, window, absolute_x,
                 absolute_y, width, height, z_index=0):
        ContentPane.__init__(self, window, absolute_x,
                             absolute_y, width, height, z_index=0)
        self.default_background = Color(127, 101, 63)
        self.default_foreground = Color(127, 0, 0)

    def render(self):
        self.print_logo()
        self.print_menu()
        self.print_footer()

    def print_logo(self):
        # TODO put logo to a file or so
        self.put_text(
            10,
            10,
            ' _   _ _       _     _                _       ')
        self.put_text(
            10,
            11,
            '| \ | (_)     | |   | |              | |      ')
        self.put_text(
            10,
            12,
            '|  \| |_  __ _| |__ | |_ ___ __ _ ___| |_ ___ ')
        self.put_text(
            10,
            13,
            '| . ` | |/ _` | \'_ \| __/ __/ _` / __| __/ _ \\')
        self.put_text(
            10,
            14,
            '| |\  | | (_| | | | | || (_| (_| \__ \ ||  __/')
        self.put_text(
            10,
            15,
            '|_| \_|_|\__, |_| |_|\__\___\__,_|___/\__\___|')
        self.put_text(
            10,
            16,
            '          __/ |                               ')
        self.put_text(
            10,
            17,
            '         |___/                                ')

    def print_menu(self):
        self.put_text(
            15,
            20,
            '[Enter]  Enter the world')
        self.put_text(15, 22, '  [Esc]  Exit game')

    def print_footer(self):
        version = 'Nightcaste v' + __version__
        self.put_text(
            self.width - len(version),
            self.height - 1,
            version)


class TcodConsoleRenderer:

    def __init__(self, console, title, width=80, height=55):
        self.console = console
        self.color_cache = {}
        libtcod.console_init_root(width, height, title)
        libtcod.console_set_default_foreground(self.console, libtcod.grey)
        libtcod.console_set_default_background(self.console, libtcod.black)

    def is_active(self):
        """Indicates if the console is still active.
        Wraps libtcod.console_is_window_closed()."""
        return not libtcod.console_is_window_closed()

    def clear(self):
        """Removes all content from the console"""
        libtcod.console_clear(self.console)

    def flush(self):
        """Flush the changes to screen."""
        libtcod.console_flush()

    def _get_tcod_color(self, color):
        tcod_color = self.color_cache.get(color)
        if tcod_color is None:
            tcod_color = libtcod.Color(color.r, color.g, color.b)
            self.color_cache.update({color: tcod_color})
        return tcod_color

    def put_char(self, x, y, char, fore_color=None, back_color=None):
        fore_color = self._get_tcod_color(fore_color)
        back_color = self._get_tcod_color(back_color)
        libtcod.console_put_char_ex(
            self.console, x, y, char.encode('utf-8'), fore_color, back_color)

    def put_text(self, x, y, text, fcolor=None, bcolor=None):
        for text_index in range(0, len(text)):
            self.put_char(x + text_index, y, text[text_index], fcolor, bcolor)
