"""The engine is the main module of the game. It initializes all necessary
subsystems and runs the super loop"""
from events import EventManager
from entities import EntityManager
from input import InputController
from nightcaste import __version__
from processors import GameInputProcessor
from processors import MenuInputProcessor
from processors import WorldInitializer
from renderer import SimpleConsoleRenderer
import logging
import time

logger = logging.getLogger('engine')


def main():
    logger.info('Nightcaste v%s', __version__)
    realtime = True
    event_manager = EventManager()
    entity_manager = EntityManager()
    renderer = SimpleConsoleRenderer(event_manager, entity_manager)
    input_controller = InputController(
        not realtime, event_manager, entity_manager)
    round = 0
    prev_time = None

    # TODO Implement ProcessorManager in order to create and manage processors
    MenuInputProcessor(event_manager, entity_manager).register()
    GameInputProcessor(event_manager, entity_manager).register()
    WorldInitializer(event_manager, entity_manager).register()

    renderer.render()
    while renderer.is_active():
        if (prev_time is None):
            prev_time = time.time()
        current_time = time.time()
        time_delta = current_time - prev_time

        # TODO: event based exit
        close_game = input_controller.update_input(round, time_delta)
        if close_game:
            break
        event_manager.process_events(round)
        renderer.render()

        prev_time = current_time
    return 0
