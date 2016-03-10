"""The events module conatins all events/actions which can occur in the game.

    TODO:
        Introduce a solution (inharitance?) to represent:
            - events with no target entity
            - events with one target entity
            - events with two target entitys (src and target)

"""
import logging
import Queue


class EventManager:
    """The central event manager which stores all events to be executed."""
    logger = logging.getLogger('events.EventManager')

    def __init__(self):
        # Event queue, which is continuuously processed by process_events
        self.events = Queue.Queue()
        # self.queue = Queue.PriorityQueue()    If priority is needed
        # self.deque = collections.deque()      Super fast unbounded queue
        #                                       without locking

        # Dictionary of processors listening for events of different types
        # {'event_type': EventProcessor}
        self.listeners = {}

    def register_listener(self, event_type, process_function):
        """Register a processor to delegate the processing of a certain event
        type."""
        self.logger.debug(
            'Register processor function %s for event type %s',
            process_function,
            event_type)
        if event_type in self.listeners:
            self.listeners[event_type].append(process_function)
        else:
            self.listeners.update({event_type: [process_function]})

    def remove_listener(self, event_type, process_function):
        """Unregisters the processor for events of the specified type."""
        self.logger.debug(
            'Unregister processor function %s for event type %s',
            process_function,
            event_type)
        if event_type in self.listeners:
            try:
                self.listeners[event_type].remove(process_function)
            except ValueError:
                self.logger.debug(
                    '%s is already unregistered from %s!',
                    process_function,
                    event_type)

    def throw(self, eventIdentifier, data=None):
        """ Enqueues an event from an identifier String"""
        self.events.put(Event(eventIdentifier, data))

    def forward(self, event):
        """Enqueues an existing event."""
        self.events.put(event)

    def process_events(self):
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
        self.logger.debug('Process event %s', event)
        if event.identifier in self.listeners:
            for process_function in self.listeners[event.identifier]:
                process_function(event)


class Event:
    """Base class for all events. An Event contains the necessary information
    for a System to react accordingly."""

    def __init__(self, identifier, data=None):
        self.identifier = identifier
        self.data = data

    def __str__(self):
        result = self.identifier + " ("
        if self.data is not None:
            for prop, val in self.data.iteritems():
                result += str(prop) + ": " + str(val) + ", "
        return result[:-2] + ")"
