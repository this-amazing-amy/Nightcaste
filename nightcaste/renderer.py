"""The Rendering Framework, wrapping around the libtcod
console."""
from nightcaste import __version__
from nightcaste.events import MenuOpen
from nightcaste.processors import ViewProcessor
from nightcaste.processors import ViewProcessor
import logging
import tcod as libtcod

logger = logging.getLogger('renderer')


class SimpleConsoleRenderer:

    def __init__(self, event_manager, entity_manager, width=80, height=55):
        self.event_manager = event_manager
        self.entity_manager = entity_manager
        self.console = 0
        libtcod.console_init_root(width, height, "Nightcaste " + __version__)
        libtcod.console_set_default_foreground(self.console, libtcod.grey)
        libtcod.console_set_default_background(self.console, libtcod.black)

        # TODO move code to some GUI wor Window class which knows the renderer
        # and make the renderer itself more stupid (just wrap tcod functions)
        self.view_controller = ViewController()
        ViewProcessor(self.event_manager, self.entity_manager,
                      self.view_controller).register()
        menu_view = self.view_controller.add_view('menu')
        menu_view.add_pane('main_menu', MenuPane(self, 0, 0, width, height))
        game_view = self.view_controller.add_view('game')
        game_view.add_pane('map', MapPane(self, 0, 0, width, height - 5))
        game_view.add_pane('status', StatusPane(self, 0, height - 5, width, 5))

        # self.view_controller.show('menu')
        event_manager.enqueue_event(MenuOpen())

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
        # TODO: reverse responsibility: the view controller knows the renderer
        # and calls its methods
        self.view_controller.render()
        self.flush()

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

    def __init__(self, renderer, absolute_x,
                 absolute_y, width, height, z_index=0):
        self.renderer = renderer
        self.pos_x = absolute_x
        self.pos_y = absolute_y
        self.width = width
        self.height = height
        self.z_index = z_index

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

    def update(self):
        """Updates the internal state of the pane."""
        pass


class MapPane(ContentPane):
    """Renders every visisble component, e.g the map with all its entities"""

    def __init__(self, renderer, absolute_x,
                 absolute_y, width, height, z_index=0):
        ContentPane.__init__(self, renderer, absolute_x,
                             absolute_y, width, height, z_index=0)
        self.viewport_x = 0
        self.viewport_y = 0

    def update(self):
        """Updates the view port"""
        self._update_view_port()

    def render(self):
        """Renders all entieties with a visable renderable component and with a
        position in the current viewport."""
        em = self.renderer.entity_manager
        # TODISCUSS: list comprehension before sort ???
        renderables = {k: v for k, v in em.get_all_of_type(
            'Renderable').iteritems() if v.visible}
        for entity, renderable in sorted(
                renderables.iteritems(), key=lambda rdict: rdict[1].z_index):
            self._render_entity(entity, renderable)

    def _render_entity(self, entity, renderable):
        """Check if the position of the given entity is in the viewport and pass
        the entety to the renderer with the recalculated position in the pane.

        Args:
            entity (object): the entity which should be rendered.
            renderable (Renderable): The visible renderable component of the
                given entity.

        """
        em = self.renderer.entity_manager
        position = em.get_entity_component(entity, 'Position')
        # TODO pass own color component to the renderer and map to tcod color in
        # the latest possible moment
        fore_color = self.renderer._get_tcod_color(entity)
        if self._in_viewport(position):
            self.put_char(
                position.x - self.viewport_x,
                position.y - self.viewport_y,
                renderable.character,
                fore_color)

    def _update_view_port(self):
        """The viewport is the visble range of the map. The viewport is always
        centered on the player until it hits the edges of the map. The viewport
        is represented by a start point + width and high of the pane."""
        em = self.renderer.entity_manager
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
