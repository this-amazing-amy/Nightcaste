"""The engine is the main module of the game. It initializes all necessary
subsystems and runs the super loop"""
from events import EventManager
from entities import EntityManager
from input import InputController
from nightcaste import __version__
from processors import SystemManager
from renderer import WindowManager
from renderer import MenuPane
from renderer import MapPane
from renderer import StatusPane
import logging
import time

logger = logging.getLogger('engine')


def main():
    logger.info('Nightcaste v%s', __version__)
    realtime = True
    event_manager = EventManager()
    entity_manager = EntityManager()
    system_manager = SystemManager(
        event_manager,
        entity_manager,
        get_systems_config())
    input_controller = InputController(
        not realtime, event_manager, entity_manager)
    window_manager = WindowManager(event_manager, entity_manager)
    window = create_window(window_manager)
    round = 0
    prev_time = None

    event_manager.throw("MenuOpen")
    window.render()
    while window.is_active():
        if (prev_time is None):
            prev_time = time.time()
        current_time = time.time()
        time_delta = current_time - prev_time

        # TODO: event based exit
        close_game = input_controller.update_input(round, time_delta)
        if close_game:
            break
        event_manager.process_events(round)
        system_manager.update(round, time_delta)
        window.render()

        prev_time = current_time
    return 0


def get_systems_config():
    return {
        'systems': [
            'MenuInputProcessor',
            'GameInputProcessor',
            'WorldInitializer',
            'MapChangeProcessor',
            'MovementProcessor',
            'UseEntityProcessor']}


def create_window(window_manager):
    width = 80
    height = 55
    window = window_manager.create_empty_window(
        'Nightcaste ' + __version__, width, height)

    menu_view = window.add_view('menu')
    menu_view.add_pane('main_menu', MenuPane(window, 0, 0, width, height))
    game_view = window.add_view('game')
    game_view.add_pane('map', MapPane(window, 0, 0, width, height - 5))
    game_view.add_pane('status', StatusPane(window, 0, height - 5, width, 5))
    return window
