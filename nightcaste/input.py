"""This module handles user inputs and transforms then into key codes"""
import tcod as libtcod


def wait_for_input(flush):
    """This function waits for the user to press a key. It returns the code of
    the key pressed as well as the corresponding character. See documentation
    for TCOD_key_t.

        Args:
            flush (bool): If the flush parameter is true, every pending keypress
            event is discarded, then the function wait for a new keypress. If
            flush is false, the function waits only if there are no pending
            keypress events, else it returns the first event in the keyboard
            buffer.


    """
    return libtcod.console_wait_for_keypress(flush)
