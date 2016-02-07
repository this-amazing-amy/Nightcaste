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

logger = logging.getLogger('engine')


def main():
    logger.info('Nightcaste v%s', __version__)
    event_manager = EventManager()
    entity_manager = EntityManager()
    renderer = SimpleConsoleRenderer(entity_manager)
    input_controller = InputController(entity_manager)
    round = 0

    # TODO Dummy: will be triggered from main menu
    MenuInputProcessor(event_manager, entity_manager).register()
    WorldInitializer(event_manager, entity_manager).register()

    renderer.render()
    while renderer.is_active():
        round += 1
        logger.info('Round: %s', round)
        # TODISCUSS: Pass the and entity manager to input?
        input_event = input_controller.get_event()
        if input_event is False:
            break
        event_manager.enqueue_event(input_event)
        event_manager.process_events(round)
        renderer.render()

    return 0
