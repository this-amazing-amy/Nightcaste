"""The engine is the main module of the game. It initializes all necessary
subsystems and runs the super loop"""
from renderer import SimpleConsoleRenderer
# from events import EventManager
from entities import EntityManager
import input


def main():
    # event_manager = EventManager()
    entity_manager = EntityManager()
    renderer = SimpleConsoleRenderer(entity_manager)

    renderer.render()
    while renderer.is_active():
        # Hook up Player Movement System with the Keyboard Input
        input.wait_for_input(True)
        renderer.render()

    return 0
