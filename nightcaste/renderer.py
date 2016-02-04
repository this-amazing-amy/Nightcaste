""" The Rendering Framework, wrapping around the libtcod
    console. """
import tcod as libtcod


class SimpleConsoleRenderer:

    def __init__(self, entity_manager):
        self.entity_manager = entity_manager
        libtcod.console_init_root(80, 50, 'Nightcaste Simple Console Renderer')
        libtcod.console_set_default_foreground(0, libtcod.white)
        libtcod.console_set_default_background(0, libtcod.black)

    def is_active(self):
        """ Indicates if the console is still active
            Wraps libtcod.console_is_window_closed() """
        return not libtcod.console_is_window_closed()

    def render(self):
        """ Renders all renderable entities to the console """
        renderables = self.entity_manager.get_all_of_type("Renderable")
        positions = self.entity_manager.get_other_components_for_entities(
         renderables, "Position")
        for entity in renderables:
            libtcod.console_clear(0)
            libtcod.console_set_char(0, positions[entity].x,
                                     positions[entity].y,
                                     renderables[entity].character)
        libtcod.console_flush()
