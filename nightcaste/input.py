"""This module handles user inputs and transforms then into key codes."""
import events
import logging
import tcod as libtcod

logger = logging.getLogger('input')


class InputController:

    def __init__(self, entity_manager):
        self.entity_manager = entity_manager
        # TODO: Make Renderer-Events (for menus, quitting, etc.)

    def get_event(self):
        """ Gets a keycode from input and returns an according event """
        event = None
        while event is None:
            key = self.wait_for_input(True)
            logger.debug('Key pressed: %s', key.vk)
            event = self.map_key_to_event(key.vk)
        logger.debug('Action created: %s', event)
        return event

    def map_key_to_event(self, keycode):
        """ Determines, which event to throw at the given key """

        # TODO Move to GameInputProcessor, MenuInputProcessor, Inventory....
        if keycode == libtcod.KEY_ENTER:
            return events.WorldEnter()
        elif keycode == libtcod.KEY_UP:
            return events.MoveAction(self.entity_manager.player, 0, -1)
        elif keycode == libtcod.KEY_DOWN:
            return events.MoveAction(self.entity_manager.player, 0, 1)
        elif keycode == libtcod.KEY_LEFT:
            return events.MoveAction(self.entity_manager.player, -1, 0)
        elif keycode == libtcod.KEY_RIGHT:
            return events.MoveAction(self.entity_manager.player, 1, 0)
        elif keycode == libtcod.KEY_ESCAPE:
            return False

        return None

    def wait_for_input(self, flush):
        """This function waits for the user to press a key. It returns the code
        of the key pressed as well as the corresponding character. See
        documentation for TCOD_key_t.

            Args:
                flush (bool): If the flush parameter is true, every pending
                keypress event is discarded, then the function wait for a new
                keypress. If flush is false, the function waits only if there
                are no pending keypress events, else it returns the first event
                in the keyboard buffer.


        """
        key = libtcod.console_wait_for_keypress(flush)
        while not libtcod.console_is_key_pressed(key.vk):
            key = libtcod.console_wait_for_keypress(flush)
        return key
