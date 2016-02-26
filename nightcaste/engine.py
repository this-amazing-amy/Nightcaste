"""The engine is the main module of the game. It initializes all necessary
subsystems and runs the super loop"""
from behaviour import BehaviourManager
from events import EventManager
from entities import EntityManager
from nightcaste import __version__
from processors import SystemManager
from renderer import MenuPane
from renderer import MapPane
from renderer import StatusPane
import game
import input
import logging
import pygame
import time
import utils

logger = logging.getLogger('engine')


def main():
    logger.info('Nightcaste v%s', __version__)

    game_config = utils.load_config('config/nightcaste.json')

    realtime = True
    pygame.init()
    event_manager = EventManager()
    entity_manager = EntityManager()
    behaviour_manager = BehaviourManager(
        event_manager,
        entity_manager,
        game_config['behaviours'])
    system_manager = SystemManager(
        event_manager,
        entity_manager,
        game_config)
    input_controller = input.InputController(
        not realtime, event_manager, entity_manager)
    window = create_window(event_manager, entity_manager)
    prev_time = None

    event_manager.throw("MenuOpen")
    while window.is_active():
        if (prev_time is None):
            prev_time = time.time()
        current_time = time.time()
        time_delta = current_time - prev_time

        if game.status != game.G_PAUSED:
            behaviour_manager.update(round, time_delta)
        request_close = input_controller.update(round, time_delta)
        if request_close or input.is_pressed(input.K_ESCAPE):
            break
        event_manager.process_events(round)
        system_manager.update(round, time_delta)
        window.render()

        prev_time = current_time
    return 0


def create_window(event_manager, entity_manager):
    gui_config = utils.load_config('config/gui.json')
    mngr_config = gui_config['window_manager']
    window_manager_class = utils.class_for_name(mngr_config[0], mngr_config[1])
    window_manager = window_manager_class(event_manager, entity_manager,
                                          gui_config)
    window = window_manager.create("nightcaste")

    # menu_view = window.add_view('menu')
    # menu_view.add_pane('main_menu', MenuPane(window, 0, 0, width, height))
    # game_view = window.add_view('game')
    # game_view.add_pane('map', MapPane(window, 0, 0, width, height - 5))
    # game_view.add_pane('status', StatusPane(window, 0, height - 5, width, 5))
    return window
