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
import random

logger = logging.getLogger('renderer')
ASSET_DIR = path.abspath(
    path.join(
        path.dirname(__file__),
        '..',
        'assets'))
TILESET_DIR = path.abspath(
    path.join(ASSET_DIR,
              'tilesets'))
SPRITE_DIR = path.abspath(
    path.join(ASSET_DIR,
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
        # TODO: Make percentage-widths possible
        self.screen = pygame.display.set_mode((config["size"][0],
                                               config["size"][1]))
        self.image_manager = ImageManager(ASSET_DIR)
        self.sprite_manager = SpriteManager(self.image_manager)
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
        logger.debug('show %s', name)
        """Shows the specified view."""
        changed = False
        if name in self.views:
            changed = True
            self._activate_view(name)
        return changed

    def _activate_view(self, name):
        self.active_view = name
        for pane_name in self.views[self.active_view]:
            self.panes[pane_name].initialize()

    def add_pane(self, pane):
        conf = self.config['panes'][pane]
        pane_class = utils.class_for_name(conf['impl'][0], conf['impl'][1])
        self.panes[pane] = pane_class(self, conf['position'][0],
                                      conf['position'][1],
                                      conf['size'][0],
                                      conf['size'][1],
                                      conf.get('layer', 0))
        logger.debug('Added Pane: %s', self.panes[pane])

    def is_active(self):
        return True

    def render(self):
        dirty = []
        for pane_name in self.views[self.active_view]:
            pane = self.panes[pane_name]
            pane.render()
            self.screen.blit(pane.surface, (pane.x, pane.y))
            dirty.extend(pane.dirty_rects)
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

    def put_image(self, x, y, name, fit=False):
        image = self.window.image_manager._load_image(name)
        if fit:
            image = pygame.transform.scale(image, (self.surface.get_width(),
                                                   self.surface.get_height()))
        self.surface.blit(image, (x, y))

    def render(self):
        pass

    def update(self):
        pass


class ScrollablePane(ContentPane):

    def __init__(self, window, x, y, width, height, z_index=0):
        super(ScrollablePane, self).__init__(window, x, y,
                                             width, height, z_index=0)
        self.image = None
        self.viewport = ViewPort(width, height)

    def initialize(self):
        self.viewport.rect.x = 0
        self.viewport.rect.y = 0

    def update_viewport(self, target_x, target_y):
        dx, dy = self.viewport.calculate_scroll(target_x, target_y)
        self.scroll(dx, dy)

    def scroll(self, dx, dy):
        if (dx, dy) == (0, 0):
            return

        view_rect = self.surface.get_rect()
        port_rect = self.viewport.rect
        self.surface.scroll(dx, 0)
        if dx < 0:
            # sroll right (image moves left)
            self.viewport.rect.move_ip((-dx, 0))
            src_rect = port_rect.copy()
            src_rect.w = -dx
            src_rect.right = port_rect.right
            dst_rect = view_rect.copy()
            dst_rect.w = -dx
            dst_rect.right = view_rect.right
            self._blit_scroll(src_rect, dst_rect)
        elif dx > 0:
            # scroll left (image moves right)
            self.viewport.rect.move_ip((-dx, 0))
            src_rect = port_rect.copy()
            src_rect.w = dx
            dst_rect = view_rect.copy()
            dst_rect.w = dx
            self._blit_scroll(src_rect, dst_rect)

        self.surface.scroll(0, dy)
        port_rect = self.viewport.rect
        if dy < 0:
            # scroll down (image moves up)
            self.viewport.rect.move_ip((0, -dy))
            src_rect = port_rect.copy()
            src_rect.h = -dy
            src_rect.bottom = port_rect.bottom
            dst_rect = view_rect.copy()
            dst_rect.h = -dy
            dst_rect.bottom = view_rect.bottom
            self._blit_scroll(src_rect, dst_rect)
        elif dy > 0:
            # scroll up (image moves down)
            self.viewport.rect.move_ip((0, -dy))
            src_rect = port_rect.copy()
            src_rect.h = dy
            dst_rect = view_rect.copy()
            dst_rect.h = dy
            self._blit_scroll(src_rect, dst_rect)

    def _blit_scroll(self, src_rect, dst_rect):
        """Clips src_rect with image and blits the remaining image to the
        adjusted destionation.
        If the src_rect does not overlay the image, the destionation will be
        filled with the default background color.
        If the src_rect completly fits into the image, the subimage will be
        blitted to the unaltered destination.
        If the src_rect only overlays parts of the image, the source and
        destination will be adjusted."""
        image_rect = self.image.get_rect()
        sub_rect = src_rect.clip(image_rect)
        if sub_rect.w == 0 and sub_rect.h == 0:
            # src does not overlap image
            self.print_background(rect=dst_rect)
            self.dirty_rects.append(self.surface.get_rect())
            return

        if src_rect.left < sub_rect.left or src_rect.right > sub_rect.right:
            # src overlaps to the left and/or right
            dst_rect.left = sub_rect.left - src_rect.left
            dst_rect.w = sub_rect.w
        if src_rect.top < sub_rect.top or src_rect.bottom < sub_rect.bottom:
            # src overlaps to the top and/or buttom
            dst_rect.top = sub_rect.top - src_rect.top
            dst_rect.h = sub_rect.h
        self.surface.blit(self.image.subsurface(sub_rect), dst_rect)
        self.dirty_rects.append(self.surface.get_rect())

    def put_bg_image(self, image, x, y):
        """Blits an image to the background. If the position is in the current
        viewport, the image will also be blitted to the current surface."""
        self.image.blit(image, (x, y))
        if self.viewport.contains(x, y):
            x_off, y_off = self.viewport.offset(x, y)
            rects = self.surface.blit(image, (x_off, y_off))
            self.dirty_rects.append(rects)

    def put_sprite(self, sprite):
        sprite.rect = self.viewport.apply(sprite.rect)
        super(ScrollablePane, self).put_sprite(sprite)


class TiledPane(ScrollablePane):

    def __init__(self, window, x, y, width, height, z_index=0):
        super(TiledPane, self).__init__(window, x, y, width, height, z_index=0)
        # put to pane configuration
        tile_config = utils.load_config('config/tilesets/tiles.json')
        self.tileset = TileSet(window.image_manager, tile_config)

    def put_tile(self, x, y, tile_name):
        tile = self.tileset.get_tile(tile_name)
        super(TiledPane, self).put_bg_image(
            tile,
            x * self.tileset.tile_width,
            y * self.tileset.tile_height)

    def put_sprite(self, sprite):
        sprite.rect.x = sprite.rect.x * self.tileset.tile_width
        sprite.rect.y = sprite.rect.y * self.tileset.tile_height
        super(TiledPane, self).put_sprite(sprite)

    def update_viewport(self, target_x, target_y):
        super(TiledPane, self).update_viewport(
            target_x * self.tileset.tile_width,
            target_y * self.tileset.tile_height)

    def create_bg(self, width, height):
        self.image = pygame.Surface((
            width * self.tileset.tile_width,
            height * self.tileset.tile_height))


class MapPane(TiledPane):
    """Renders every visible component, e.g the map with all its entities"""

    def __init__(self, window, x, y, width, height, z_index=0):
        TiledPane.__init__(self, window, x, y, width, height, z_index=0)

    def initialize(self):
        super(MapPane, self).initialize()
        self._render_map()

    def update(self):
        """Updates the view port"""
        self._update_view_port()

    def render(self):
        """Renders all entities with a visible renderable component and with a
        position in the current viewport."""
        self._render_sprites()
        return self.dirty_rects

    def _render_map(self):
        self.print_background()
        em = self.window.entity_manager
        if em.current_map is not None:
            map = em.get(em.current_map, 'Map')
            self.create_bg(map.width(), map.height())
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

    def _render_sprite(self, entity, sprite, position):
        # restore map tile at old position
        if sprite.dirty > 0:
            em = self.window.entity_manager
            old_tile_entity = em.get_current_map()[position.x_old][
                position.y_old]
            old_tile = em.get(old_tile_entity, 'Tile')
            self.put_tile(
                position.x_old,
                position.y_old,
                old_tile.name)
            # render sprite at new position
            sprite.rect.x = position.x
            sprite.rect.y = position.y
            self.put_sprite(sprite)

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
        self.put_tile(position.x, position.y, tile.name)

    def _update_view_port(self):
        """The viewport is the visble range of the map. The viewport is always
        centered on the player until it hits the edges of the map. The viewport
        is represented by a start point + width and high of the pane."""
        em = self.window.entity_manager
        # map = em.get(em.current_map, 'Map')
        player_pos = em.get(em.player, 'Position')
        self.update_viewport(player_pos.x, player_pos.y)


class ViewPort:

    def __init__(self, width, height):
        self.rect = pygame.Rect(0, 0, width, height)

    def contains(self, x, y):
        """Return wether the point is in the current viewport."""
        return self.rect.collidepoint(x, y)

    def apply(self, rect):
        """Apply the viewport offset to a rect."""
        rect.x -= self.rect.x
        rect.y -= self.rect.y
        return rect

    def offset(self, x, y):
        """Add the viewport offset to a point."""
        return (x - self.rect.x, y - self.rect.y)

    def calculate_scroll(self, target_x, target_y):
        """Calcualtes the scroll needed to center the target."""
        l_old = self.rect.x
        t_old = self.rect.y
        l = target_x - int(self.rect.w / 2)
        t = target_y - int(self.rect.h / 2)
        return (l_old - l, t_old - t)

    def calculate_scroll_compl(self, player_pos, map):
        """UNTESTED."""
        x_old = self.rect.x
        y_old = self.rect.y
        if map.width() > self.rect.w:
            self.rect.x = max(player_pos.x - int(self.rect.w / 2), 0)
            self.rect.x += min(map.width() - (self.rect.x + self.rect.w), 0)
        else:
            self.rect.x = int((self.rect.w - map.width()) / 2)

        if map.height() > self.rect.h:
            self.rect.y = max(player_pos.y - int(self.rect.h / 2), 0)
            self.rect.y += min(map.height() - (self.rect.y + self.rect.h), 0)
        else:
            self.rect.y = int((self.rect.h - map.height()) / 2)

        return (self.rect.x - x_old, self.rect.y - y_old)


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
        pass
        # self.put_image(0, 0, "gui/main_menu.png", True)

    def print_menu(self):
        self.put_text(
            400,
            380,
            '[Enter]  Enter the world')
        self.put_text(400, 400, '  [Esc]  Exit game')

    def print_footer(self):
        version = 'Nightcaste v' + __version__
        self.put_text(
            self.width - len(version) * 5,
            self.height - 50,
            version)


class TileSet:

    def __init__(self, image_manager, config):
        self.tiles = {}
        general_config = config['general']
        self.tile_width = general_config['tile_width']
        self.tile_height = general_config['tile_height']
        image_path = general_config['image']
        tile_table = image_manager.load_image_sheet(
            image_path, self.tile_width, self.tile_height)
        tile_definitions = config['tiles']
        for tile_def in tile_definitions:
            key = tile_def['key']
            tableposition = tile_def['position']
            tile = tile_table[tableposition[0]][tableposition[1]]
            self.add_tile(key, tile)

    def add_tile(self, key, tile):
        if key in self.tiles:
            self.tiles[key] = self.tiles[key] + [tile]
        else:
            self.tiles[key] = [tile]

    def get_tile(self, key):
        return random.sample(self.tiles[key], 1)[0]


class ImageManager:

    def __init__(self, asset_dir=ASSET_DIR):
        self.asset_dir = asset_dir
        self.image_cache = {}

    def load_image(self, name, cache=True):
        dir = name.split("/")
        filename = ASSET_DIR
        for d in dir:
            filename = path.join(filename, d)
        image = pygame.image.load(filename).convert_alpha()
        if cache:
            self.image_cache[name] = image
        return image

    def load_image_sheet(self, file_name, tile_width, tile_height, cache=True):
        sheet = self.load_image(file_name, cache)
        image_width, image_height = sheet.get_size()
        tile_table = []
        for tile_x in range(0, image_width / tile_width):
            line = []
            tile_table.append(line)
            for tile_y in range(0, image_height / tile_height):
                rect = (
                    tile_x * tile_width,
                    tile_y * tile_height,
                    tile_width,
                    tile_height)
                line.append(sheet.subsurface(rect))
        return tile_table

    def get(self, key):
        return self.images[key]


class SpriteManager:

    def __init__(self, image_manager):
        self.images = {}
        self.image_manager = image_manager

    def initialize_sprite(self, sprite):
        image = self.images.get(sprite.name)
        if image is None:
            image = self._load_sprite(sprite.name)
        sprite.image = image.copy()
        sprite.rect = image.get_rect()
        logger.debug('Sprite initialized %s', sprite)

    def _load_sprite(self, name):
        """Assume the name is a direct path to an image containing exactly the
        required sprite image.
        TODO: Support load_by_config which can load a complete sprite set from
        configuration like with a TileSet."""
        # TEST
        sprite_sheet = self.image_manager.load_image_sheet('sprites/player.png', 32, 32)
        return sprite_sheet[0][0]
