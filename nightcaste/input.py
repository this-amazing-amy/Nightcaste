"""This module handles user inputs and transforms then into key codes"""
import tcod as libtcod
import events


def get_event(entity_manager):
    """ Gets a keycode from input and returns an according event """
    event = None
    while event is None:
        key = wait_for_input(True)
        event = map_key_to_event(key.vk, entity_manager)
    return event


def map_key_to_event(keycode, entity_manager):
    """ Determines, which event to throw at the given key """
    key_actions = {
        libtcod.KEY_UP: events.MoveAction(entity_manager.player, 0, -1),
        libtcod.KEY_DOWN: events.MoveAction(entity_manager.player, 0, 1),
        libtcod.KEY_LEFT: events.MoveAction(entity_manager.player, -1, 0),
        libtcod.KEY_RIGHT: events.MoveAction(entity_manager.player, 1, 0),
        # TODO: Make Renderer-Events (for menus, quitting, etc.)
        libtcod.KEY_ESCAPE: False
    }
    return key_actions.get(keycode, None)


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
