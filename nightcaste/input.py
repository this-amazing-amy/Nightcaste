"""This module handles user inputs and transforms then into key codes"""
import events
import logging
import tcod as libtcod

logger = logging.getLogger('input')


class InputController:

    def __init__(self, entity_manager):
        self.key_actions = {
            libtcod.KEY_UP: events.MoveAction(entity_manager.player, 0, -1),
            libtcod.KEY_DOWN: events.MoveAction(entity_manager.player, 0, 1),
            libtcod.KEY_LEFT: events.MoveAction(entity_manager.player, -1, 0),
            libtcod.KEY_RIGHT: events.MoveAction(entity_manager.player, 1, 0),
            # TODO: Make Renderer-Events (for menus, quitting, etc.)
            libtcod.KEY_ESCAPE: False
        }

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
        """
        # Only map downstrokes
        if not libtcod.console_is_key_pressed(keycode):
            return None
        """
        return self.key_actions.get(keycode, None)

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
