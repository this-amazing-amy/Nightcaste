"""This module handles user inputs and transforms then into key codes."""
import logging
import pygame

logger = logging.getLogger('input')

K_ENTER = pygame.K_RETURN
K_ESCAPE = pygame.K_ESCAPE
K_DOWN = pygame.K_DOWN
K_LEFT = pygame.K_LEFT
K_RIGHT = pygame.K_RIGHT
K_UP = pygame.K_UP


def is_pressed(code):
    return pygame.key.get_pressed()[code]


class InputController:

    def __init__(self, blocking, event_manager, entity_manager):
        self.blocking = blocking
        self.entity_manager = entity_manager
        self.event_manager = event_manager
        self.request_close = False

    def update(self, rounds, delta_time):
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
        return self.request_close

    def check_for_input(self):
        """ Returns the last key pressed. Returns KEY_NONE if no key was
        pressed."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                self.request_close = True
            elif event.type == pygame.KEYDOWN:
                self.event_manager.throw('KeyPressed', {'keycode': event.key})

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
        # TODO check blocking input with pygame
        pass
