"""The engine is the main module of the game. It initializes all necessary
subsystems and runs the super loop"""
from events import EventManager
from entities import EntityManager
from entities import EntityConfiguration
from input import InputController
from nightcaste import __version__
from processors import MovementProcessor
from renderer import SimpleConsoleRenderer
import logging

logger = logging.getLogger('engine')


def main():
    logger.info('Nightcaste v%s', __version__)
    event_manager = EventManager()
    entity_manager = EntityManager()
    renderer = SimpleConsoleRenderer(entity_manager)
    round = 0l

    # Creating Player from Configuration
    # TODO: Make a Player Blueprint
    player_config = EntityConfiguration()
    player_config.add_attribute("Position", "x", 0)
    player_config.add_attribute("Position", "y", 0)
    player_config.add_attribute("Renderable", "character", "@")
    entity_manager.player = entity_manager.create_entity_from_configuration(
        player_config)
    input_controller = InputController(entity_manager)
    # TODISCUSS: Do we need to save the Listeners?
    event_manager.register_listener(
        "MoveAction", MovementProcessor(
            event_manager, entity_manager))
    renderer.render()
    while renderer.is_active():
        round += 1l
        logger.info('Round: %s', round)
        # TODISCUSS: Pass the and entity manager to input?
        input_event = input_controller.get_event()
        if input_event is False:
            break
        event_manager.enqueue_event(input_event)
        event_manager.process_events(round)
        renderer.render()

    return 0
