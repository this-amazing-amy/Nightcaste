"""The engine is the main module of the game. It initializes all necessary
subsystems and runs the super loop"""
from events import EventManager
from entities import EntityManager
from input import InputController
from nightcaste import __version__
from processors import WorldInitializer
from processors import MenuInputProcessor
from renderer import SimpleConsoleRenderer
import logging
import time

logger = logging.getLogger('engine')


def main():
    logger.info('Nightcaste v%s', __version__)
    event_manager = EventManager()
    entity_manager = EntityManager()
    renderer = SimpleConsoleRenderer(entity_manager)
    input_controller = InputController(entity_manager)
    round = 0
    prev_time = None

    # TODO Dummy: will be triggered from main menu
    MenuInputProcessor(event_manager, entity_manager).register()
    WorldInitializer(event_manager, entity_manager).register()

    renderer.render()
    while renderer.is_active():
        if (prev_time is None):
            prev_time = time.time()
        current_time = time.time()
        time_delta = current_time - prev_time

        logger.info('Round: %s, Time passed: %s', round, time_delta)

        # TODISCUSS: Pass the and entity manager to input?
        input_event = input_controller.get_event(True)
        if input_event is False:
            break
        event_manager.enqueue_event(input_event)
        event_manager.process_events(round)
        renderer.render()

        prev_time = current_time
    return 0
