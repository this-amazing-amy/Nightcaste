"""The events module conatins all events/actions which can occur in the game.

    TODO:
        Introduce a solution (inharitance?) to represent:
            - events with no target entity
            - events with one target entity
            - events with two target entitys (src and target)

"""
import Queue


class EventManager:
    """The central event manager which stores all events to be executed."""

    def __init__(self):
        # Event queue, which is continuuously processed by process_events
        self.queue = Queue()
        # Dictionary of systems listening for events of different types
        # {'event_type': System}
        self.listeners = {}

    def register_listener(self, system, event_type):
        pass

    def remove_listener(self, system, event_type):
        pass

    def purge_listener(self, system):
        pass

    def enqueue_event(self, event):
        pass

    def process_events(self, round):
        pass


class Event:
    """Base class for all events. An Event contains the necessary information
    for a System to react accordingly."""

    def type(self):
        """Returns the class name of the event"""
        return self.__class__.__name__


class MoveAction(Event):
    """This action indicates that an entity should be moved.

    Args:
        entity (long): The entity which should be moved.
        dx (int): The distance to move horizontal.
        dy (int): The distance to move vertical.

    """

    def __init__(self, entity, dx, dy):
        self.entity = entity
        self.dx = dx
        self.dy = dy
