"""The Rendering Framework, wrapping around the libtcod
console."""
from nightcaste import __version__
from nightcaste.components import Color
from nightcaste.processors import SpriteProcessor
from nightcaste.processors import ViewProcessor
from os import path
import game
import logging
import pygame
import utils

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


class WindowManager:
    """ Creates and administrates Window instances """

    def __init__(self, event_manager, entity_manager, config):
        self.windows = []
        self.event_manager = event_manager
        self.entity_manager = entity_manager
        self.config = config

    def create(self, name):
        conf = self.config["windows"][name]
        window_class = utils.class_for_name(conf['impl'][0], conf['impl'][1])
        window = window_class(conf, self.event_manager, self.entity_manager)
        self.windows.append(window)
        return window


class Window:
    """A window an which something can be rendered. Supports multiple views with
    content panes in them."""

    def __init__(self, config, event_manager, entity_manager):
        self.config = config
        self.event_manager = event_manager
        self.entity_manager = entity_manager
        self.sprite_manager = SpriteManager()
        # TODO: Make percentage-widths possible
        self.screen = pygame.display.set_mode((config["size"][0],
                                               config["size"][1]))
        self.panes = {}
        self.views = self.initialize_views(self.config["views"])
        self.active_view = self.config["default_view"]

        ViewProcessor(
            event_manager,
            entity_manager,
            self).register()

        SpriteProcessor(
            event_manager,
            entity_manager,
            self.sprite_manager).register()

    def initialize_views(self, views):
        result = {}
        for view in views:
            result[view] = []
            for pane in views[view]:
                result[view].append(pane)
                self.add_pane(pane)
        return result

    def update_view(self, name):
        view = self.views.get(name, None)
        if view is not None:
            for pane in view:
                self.panes[pane].update()

    def show(self, name):
        print 'show %s' % (name)
        """Shows the specified view."""
        changed = False
        if self.active_view == name:
            changed = True
        self.active_view = name
        return changed

    def add_pane(self, pane):
        conf = self.config['panes'][pane]
        pane_class = utils.class_for_name(conf['impl'][0], conf['impl'][1])
        self.panes[pane] = pane_class(self, conf['position'][0],
                                      conf['position'][1],
                                      conf['size'][0],
                                      conf['size'][1],
                                      conf.get('layer', 0))

    def is_active(self):
        return True

    def render(self):
        dirty = []
        for pane_name in self.views[self.active_view]:
            pane = self.panes[pane_name]
            pane.render()
            self.screen.blit(pane.surface, (pane.x, pane.y))
            dirty += pane.dirty_rects
            pane.dirty_rects = []
        pygame.display.update(dirty)


class ContentPane(object):
    """Can be printed with colored text"""

    def __init__(self, window, x,
                 y, width, height, z_index=0):
        self.window = window
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.z_index = z_index
        self.default_background = Color(0, 0, 0)
        self.default_foreground = Color(175, 175, 175)
        self.surface = pygame.Surface((width, height))
        # TODO: Cache font centrally in window
        # TODO: Make Font size dynamic/configurable
        self.font = pygame.font.Font(None, 15)
        self.dirty_rects = []

    def initialize(self):
        logger.debug('initialize %s', self)
        self.print_background()

    def print_background(self, color=None, rect=None):
        if color is None:
            color = self.default_background
        if rect is None:
            rect = (0, 0, self.width, self.height)

        rects = self.surface.fill((color.r, color.g, color.b),
                                  pygame.Rect(rect[0], rect[1],
                                              rect[2], rect[3]))
        self.dirty_rects.append(rects)

    def put_text(self, x, y, text, fcolor=None, bcolor=None):
        if fcolor is None:
            fcolor = self.default_foreground
        if bcolor is None:
            bcolor = self.default_background
        text = self.font.render(text, True,
                                (fcolor.r, fcolor.g, fcolor.b),
                                (bcolor.r, bcolor.g, bcolor.b))
        dirty_text = self.surface.blit(text, (x, y))
        self.dirty_rects.append(dirty_text)

    def put_sprite(self, sprite):
        if sprite.visible:
            rects = self.surface.blit(sprite.image, sprite.rect)
            self.dirty_rects.append(rects)
            # TODO let handle pygame the dirty flags by using sprite groups
            sprite.dirty = 0

    def render(self):
        pass

    def update(self):
        pass


class MapPane(ContentPane):
    """Renders every visible component, e.g the map with all its entities"""

    def __init__(self, window, x, y, width, height, z_index=0):
        ContentPane.__init__(self, window, x, y, width, height, z_index=0)
        self.viewport_x = 0
        self.viewport_y = 0
        self.viewport_dirty = True
        # put to pane configuration
        tileset_config = utils.load_config('config/tilesets/ascii.json')
        self.tileset = TileSet(tileset_config)
        self.tileset.configure_tiles(tileset_config)

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
        return self.dirty_rects

    def put_tile(self, x, y, tile_name):
        tile = self.tileset.get_tile(tile_name)
        rects = self.surface.blit(
            tile,
            (x * self.tileset.tile_width,
             y * self.tileset.tile_height))
        self.dirty_rects.append(rects)

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

    def __init__(self, window, x, y, width, height, z_index=0):
        ContentPane.__init__(self, window, x, y, width, height, z_index=0)
        self.default_background = Color(127, 101, 63)
        self.default_foreground = Color(127, 0, 0)

    def render(self):
        self.print_background()
        self.print_logo()
        self.print_menu()
        self.print_footer()
        return self.dirty_rects

    def print_logo(self):
        # TODO Use an image
        self.put_text(
            400,
            300,
            'NIGHTCASTE')

    def print_menu(self):
        self.put_text(
            400,
            380,
            '[Enter]  Enter the world')
        self.put_text(400, 400, '  [Esc]  Exit game')

    def print_footer(self):
        version = 'Nightcaste v' + __version__
        self.put_text(
            self.width - len(version)*5,
            self.height - 50,
            version)


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
