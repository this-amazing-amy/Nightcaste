"""The events module conatins all events/actions which can occur in the game.

    TODO:
        Introduce a solution (inharitance?) to represent:
            - events with no target entity
            - events with one target entity
            - events with two target entitys (src and target)

"""
import logging
import Queue

logger = logging.getLogger('events')


class EventManager:
    """The central event manager which stores all events to be executed."""

    def __init__(self):
        # Event queue, which is continuuously processed by process_events
        self.events = Queue.Queue()
        # self.queue = Queue.PriorityQueue()    If priority is needed
        # self.deque = collections.deque()      Super fast unbounded queue
        #                                       without locking

        # Dictionary of systems listening for events of different types
        # {'event_type': System}
        self.listeners = {}

    def register_listener(self, event_type, event_processor):
        """Register a processor to delegate the processing of a certain event
        type."""
        logger.debug(
            'Register processor %s for event type %s',
            event_processor,
            event_type)
        if event_type in self.listeners:
            self.listeners[event_type].append(event_processor)
        else:
            self.listeners.update({event_type: [event_processor]})

    def remove_listener(self, event_type, event_processor):
        "Unregisters the processor for events of the specified type."
        logger.debug(
            'Unregister processor %s for event type %s',
            event_processor,
            event_type)
        if event_type in self.listeners:
            self.listeners[event_type].remove(event_processor)

    def enqueue_event(self, event, rounds=0):
        """Enques an event which will be processed later"""
        self.events.put(event)

    def process_events(self, round):
        """Process all events in the queue.

            Args:
                round (long): The current round in the game.

            Returns:
                The number of process events in this round.

        """
        processed_events = 0
        while not self.events.empty():
            self.process_event(self.events.get_nowait(), round)
            processed_events += 1
        return processed_events

    def process_event(self, event, round):
        """Process a single event by delegating it to all registered processors.

            Args:
                event(Event): The event to be processed.
                round (long): The current round in the game.

        """
        logger.debug('Process event %s', event)
        if event.type() in self.listeners:
            for processor in self.listeners[event.type()]:
                processor.handle_event(event, round)


class Event:
    """Base class for all events. An Event contains the necessary information
    for a System to react accordingly."""

    def type(self):
        """Returns the class name of the event"""
        return self.__class__.__name__

    def __str__(self):
        return self.type()


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

    def __str__(self):
        return '%s(%s, %s, %s)' % (self.type(), self.entity, self.dx, self.dy)
