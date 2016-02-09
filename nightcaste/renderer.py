"""The Rendering Framework, wrapping around the libtcod
console."""
from nightcaste import __version__
import tcod as libtcod


class SimpleConsoleRenderer:

    def __init__(self, entity_manager, width=80, height=55):
        self.entity_manager = entity_manager
        self.console = 0
        libtcod.console_init_root(
            width, height, "Nightcaste Simple Console Renderer")
        libtcod.console_set_default_foreground(self.console, libtcod.white)
        libtcod.console_set_default_background(self.console, libtcod.black)
        self.menu_view = RenderableContainer()
        self.menu_view.add_child(MenuPane(self, 0, 0, width, height))
        self.game_view = RenderableContainer()
        self.game_view.add_child(MapPane(self, 0, 0, width, height-5))
        self.game_view.add_child(StatusPane(self, 0, height-5, width, 5))

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

    def render(self):
        self.clear()
        # TODO: Hook up Renderer to event system so the views can be switched
        # TODO: Or Make Game Status (MENU, RUNNING, PAUSED)
        if self.menu_view.active:
            self.menu_view.render()
        if self.game_view.active:
            self.game_view.render()
        self.flush()

    def render_entity(self, entity, renderable, position):
        self.put_char(
            position.x,
            position.y,
            renderable.character,
            self._get_tcod_color(entity))

    def _get_tcod_color(self, entity):
        color = self.entity_manager.get_entity_component(entity, 'Color')
        if color is not None:
            return libtcod.Color(color.r, color.g, color.b)
        return None

    def put_char(self, x, y, char, fore_color=None, back_color=None):
        if fore_color is None:
            fore_color = libtcod.console_get_default_foreground(self.console)
        if back_color is None:
            back_color = libtcod.console_get_default_background(self.console)
        libtcod.console_put_char_ex(
            self.console, x, y, char.encode('utf-8'), fore_color, back_color)

    def put_text(self, x, y, text, fcolor=None, bcolor=None):
        for text_index in range(0, len(text)):
            self.put_char(x + text_index, y, text[text_index], fcolor, bcolor)


class RenderableContainer:

    def __init__(self, active=True):
        self.active = active
        self.childs = []

    def add_child(self, child):
        self.childs.append(child)

    def render(self):
        """Renders all childs"""
        for child in self.childs:
            child.render()


class ContentPane:
    """Can be printed with colored text"""

    def __init__(self, renderer, absolute_x, absolute_y, width, height):
        self.renderer = renderer
        self.pos_x = absolute_x
        self.pos_y = absolute_y
        self.width = width
        self.height = height

    def put_char(self, x, y, char, fore_color=None, back_color=None):
        self.renderer.put_char(
            self.pos_x + x,
            self.pos_y + y,
            char,
            fore_color,
            back_color)

    def put_text(self, x, y, char, fore_color=None, back_color=None):
        self.renderer.put_text(
            self.pos_x + x,
            self.pos_y + y,
            char,
            fore_color,
            back_color)

    def print_background(self, color):
        # TODO make it better ^^
        for x in range(0, self.width):
            for y in range(0, self.height):
                self.put_char(x, y, ' ', None, color)


class MapPane(ContentPane):

    def render(self):
        em = self.renderer.entity_manager
        """Renders all renderable entities to the console."""
        renderables = em.get_all_of_type('Renderable')
        positions = em.get_components_for_entities(renderables, 'Position')
        for entity, renderable in sorted(
                renderables.items(), key=lambda rdict: rdict[1].z_index):
            self.renderer.render_entity(entity, renderable, positions[entity])


class StatusPane(ContentPane):

    def render(self):
        self.put_text(0, 0, 'Health: 100')


class MenuPane(ContentPane):

    def render(self):
        self.print_background(libtcod.sepia)
        self.print_logo()
        self.print_menu()
        self.print_footer()

    def print_logo(self):
        # TODO put logo to a file or so
        self.put_text(
            10,
            10,
            ' _   _ _       _     _                _       ',
            libtcod.red,
            libtcod.sepia)
        self.put_text(
            10,
            11,
            '| \ | (_)     | |   | |              | |      ',
            libtcod.red,
            libtcod.sepia)
        self.put_text(
            10,
            12,
            '|  \| |_  __ _| |__ | |_ ___ __ _ ___| |_ ___ ',
            libtcod.red,
            libtcod.sepia)
        self.put_text(
            10,
            13,
            '| . ` | |/ _` | \'_ \| __/ __/ _` / __| __/ _ \\',
            libtcod.red,
            libtcod.sepia)
        self.put_text(
            10,
            14,
            '| |\  | | (_| | | | | || (_| (_| \__ \ ||  __/',
            libtcod.red,
            libtcod.sepia)
        self.put_text(
            10,
            15,
            '|_| \_|_|\__, |_| |_|\__\___\__,_|___/\__\___|',
            libtcod.red,
            libtcod.sepia)
        self.put_text(
            10,
            16,
            '          __/ |                               ',
            libtcod.red,
            libtcod.sepia)
        self.put_text(
            10,
            17,
            '         |___/                                ',
            libtcod.red,
            libtcod.sepia)

    def print_menu(self):
        self.put_text(
            15,
            20,
            '[Enter]  Enter the world',
            libtcod.red,
            libtcod.sepia)
        self.put_text(15, 22, '  [Esc]  Exit game', libtcod.red, libtcod.sepia)

    def print_footer(self):
        version = 'Nightcaste v' + __version__
        self.put_text(
            self.width - len(version),
            self.height - 1,
            version,
            libtcod.red,
            libtcod.sepia)
