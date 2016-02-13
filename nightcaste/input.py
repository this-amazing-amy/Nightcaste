"""This module handles user inputs and transforms then into key codes."""
import logging
import tcod as libtcod

logger = logging.getLogger('input')


class InputController:

    def __init__(self, blocking, event_manager, entity_manager):
        self.blocking = blocking
        self.entity_manager = entity_manager
        self.event_manager = event_manager
        self.key = libtcod.Key()
        self.mouse = libtcod.Mouse()

    def update_input(self, rounds, delta_time):
        """Checks if the user has pressed a key and throws an appropriate
        key event.

            Returns:
                True if the user has requested an immdiate close, otherwise
                False.

        """
        if (self.blocking):
            self.wait_for_input(True)
        else:
            self.check_for_input()
        request_close = self.create_key_event()
        return request_close

    def create_key_event(self):
        """Determines, which event to throw for the given key.

            Returns:
                True if ESCAPE was pressed otherwise False.

        """
        if self.key.vk == libtcod.KEY_NONE:
            return False
        elif self.key.vk == libtcod.KEY_ESCAPE:
            return True

        # TODO pass whole tcod event or code and character and modifiers
        if self.key.pressed:
            key_event = 'KeyPressed'
        else:
            key_event = 'KeyReleased'
        logger.debug('Input Event Detected: %s', key_event)

        self.event_manager.throw(
            key_event, {
                'keycode': self.key.vk, 'char': self.key.c})
        return False

    def check_for_input(self):
        """ Returns the last key pressed. Returns KEY_NONE if no key was
        pressed."""
        libtcod.sys_check_for_event(
            libtcod.EVENT_KEY_PRESS, self.key, self.mouse)

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
        self.key = libtcod.console_wait_for_keypress(flush)
