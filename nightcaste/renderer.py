""" The Rendering Framework, wrapping around the libtcod
    console. """
import tcod as libtcod


class SimpleConsoleRenderer:

    def __init__(self, entity_manager):
        self.entity_manager = entity_manager
        self.console = 0
        libtcod.console_init_root(80, 50, "Nightcaste Simple Console Renderer")
        libtcod.console_set_default_foreground(self.console, libtcod.white)
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

    def render(self):
        """Renders all renderable entities to the console."""
        renderables = self.entity_manager.get_all_of_type('Renderable')
        positions = self.entity_manager.get_components_for_entities(
            renderables, 'Position')
        self.clear()
        for entity, renderable in renderables.iteritems():
            self._render_entity(entity, renderable, positions[entity])
        self.flush()

    def _render_entity(self, entity, renderable, position):
        libtcod.console_set_char_foreground(
            self.console,
            position.x,
            position.y,
            self._get_tcod_color(entity))
        libtcod.console_set_char(
            self.console,
            position.x,
            position.y,
            renderable.character)

    def _get_tcod_color(self, entity):
        tcod_color = libtcod.console_get_default_foreground(self.console)
        color = self.entity_manager.get_entity_component(entity, 'Color')
        if color is not None:
            tcod_color = libtcod.Color(color.r, color.g, color.b)
        return tcod_color
