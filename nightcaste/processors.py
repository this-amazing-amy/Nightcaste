"""The module contains the event processors. An event processor must register
itself in the EventManager in order to retrieve the events to process"""


class EventProcessor:
    """Base class for all processors.

        Args:
            event_manager (EventManager): The event manager for enqueuing new
                events.
            entity_manager (EntityManager): The entity manager for creating,
                destroying entities and access their properties

    """

    def __init__(self, event_manager, entity_manager):
        self.event_manager = event_manager
        self.entity_manager = entity_manager

    def handle_event(self, round, event):
        """TODO: Docstring for handle_event.

        :round: TODO
        :event: TODO
        :returns: TODO

        """
        pass
