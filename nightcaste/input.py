"""This module handles user inputs and transforms then into key codes."""
from events import KeyPressed
from events import KeyReleased
import logging
import tcod as libtcod

logger = logging.getLogger('input')


class InputController:

    def __init__(self, blocking, event_manager, entity_manager):
        self.blocking = blocking
        self.entity_manager = entity_manager
        self.event_manager = event_manager
        # TODO: Make Renderer-Events (for menus, quitting, etc.)

    def update_input(self, rounds, delta_time):
        """Checks if the user has pressed a key and throws an appropriate
        key event.

            Returns:
                True if the user has requested an immdiate close, otherwise
                False.

        """
        if (self.blocking):
            key = self.wait_for_input(True)
        else:
            key = self.check_for_input()
        request_close = self.create_key_event(key)
        return request_close

    def create_key_event(self, key):
        """Determines, which event to throw for the given key.

            Returns:
                True if ESCAPE was pressed otherwise False.

        """
        if key.vk == libtcod.KEY_NONE:
            return False
        elif key.vk == libtcod.KEY_ESCAPE:
            return True

        # TODO pass whole tcod event or code and character and modifiers
        if key.pressed:
            key_event = KeyPressed(key.vk)
        else:
            key_event = KeyReleased(key.vk)
        logger.debug('Input Event Detected: %s', key_event)

        self.event_manager.enqueue_event(key_event)
        return False

    def check_for_input(self):
        """ Returns the last key pressed. Returns KEY_NONE if no key was
        pressed."""
        key = libtcod.Key()
        mouse = libtcod.Mouse()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)
        return key

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
        return libtcod.console_wait_for_keypress(flush)
