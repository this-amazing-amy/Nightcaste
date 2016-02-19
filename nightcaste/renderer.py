"""The Rendering Framework, wrapping around the libtcod
console."""
from nightcaste import __version__
from nightcaste.components import Color
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


class PygameRenderer:

    def __init__(self, console, title, width=80, height=55):
        self.console = console
        self.color_cache = {}

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
        pygame.display.update()

    def put_char(self, x, y, char, fore_color=None, back_color=None):
        tile = self.tileset.get_tile(char)
        rects = self.surface.blit(
            tile,
            (x * self.tileset.tile_width,
             y * self.tileset.tile_height))

    def fill_background(self, color, rect=None):
        rects = self.surface.fill((color.r, color.g, color.b),
                          pygame.Rect(rect[0]*self.tileset.tile_width,
                                      rect[1]*self.tileset.tile_height,
                                      rect[2]*self.tileset.tile_width,
                                      rect[3]*self.tileset.tile_height))

    def put_text(self, x, y, text, fcolor=None, bcolor=None):
        for text_index in range(0, len(text)):
            self.put_char(x + text_index, y, text[text_index], fcolor, bcolor)


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
        image = pygame.image.load(filename).convert_alpha()
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
        self.renderer = PygameRenderer(number, title, width, height)
        ViewProcessor(
            event_manager,
            entity_manager,
            self.view_controller).register()

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


class ContentPane:
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
        self.print_background()

    def put_char(self, x, y, char, fore_color=None, back_color=None):
        self.window.put_char(
            self.pos_x + x,
            self.pos_y + y,
            char,
            self.default_foreground if fore_color is None else fore_color,
            self.default_background if back_color is None else back_color)

    def put_text(self, x, y, text, fore_color=None, back_color=None):
        # As long as we use tansparant tiles for printing text we have to
        # print the background to overwrite existing chars
        self.print_background(rect=(self.pos_x + x, self.pos_y + y, len(text), 1))
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
            rect = (self.pos_x+rect[0], self.pos_y+rect[1], rect[2], rect[3])

        self.window.fill_background(color, rect)

    def update(self):
        """Updates the internal state of the pane."""
        pass


class MapPane(ContentPane):
    """Renders every visisble component, e.g the map with all its entities"""

    def __init__(self, window, absolute_x,
                 absolute_y, width, height, z_index=0):
        ContentPane.__init__(self, window, absolute_x,
                             absolute_y, width, height, z_index=0)
        self.viewport_x = 0
        self.viewport_y = 0

    def update(self):
        """Updates the view port"""
        self._update_view_port()

    def render(self):
        """Renders all entieties with a visable renderable component and with a
        position in the current viewport."""
        em = self.window.entity_manager
        # TODISCUSS: list comprehension before sort ???
        renderables = {k: v for k, v in em.get_all_of_type(
            'Renderable').iteritems() if v.visible}
        positions = em.get_all_of_type('Position')
        colors = em.get_all_of_type('Color')
        self.print_background()
        for entity, renderable in sorted(
                renderables.iteritems(), key=lambda rdict: rdict[1].z_index):
            self._render_entity(
                renderable,
                positions[entity],
                colors[entity])

    def _render_entity(self, renderable, position, color):
        """Check if the position of the given entity is in the viewport and
        render the entety to the window with the recalculated position in the
        pane.

        Args:
            entity (object): the entity which should be rendered.
            renderable (Renderable): The visible renderable component of the
                given entity.

        """
        if self._in_viewport(position):
            self.put_char(
                position.x - self.viewport_x,
                position.y - self.viewport_y,
                renderable.character,
                color)

    def _update_view_port(self):
        """The viewport is the visble range of the map. The viewport is always
        centered on the player until it hits the edges of the map. The viewport
        is represented by a start point + width and high of the pane."""
        em = self.window.entity_manager
        map = em.get_entity_component(em.current_map, 'Map')
        player_pos = em.get_entity_component(em.player, 'Position')
        self.viewport_x = max(player_pos.x - int(self.width / 2), 0)
        self.viewport_y = max(player_pos.y - int(self.height / 2), 0)
        self.viewport_x += min(map.width() - (self.viewport_x + self.width), 0)
        self.viewport_y += min(map.height() -
                               (self.viewport_y + self.height), 0)

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
