"""Tests events. Propably not mutch to do here since events are mostly simple
data transfer objects"""
import pytest
from nightcaste.entities import EntityManager
from nightcaste.events import Event
from nightcaste.events import EventManager
from nightcaste.events import MoveAction
from nightcaste.processors import EventProcessor


@pytest.fixture
def event_manager():
    return EventManager()


@pytest.fixture
def entity_manager():
    return EntityManager()


class TestEvent:

    def test_type(self):
        """Tests if events return their correct type"""
        event = Event()
        move = MoveAction(42, 1, -1)

        assert event.type() == 'Event'
        assert move.type() == 'MoveAction'


class TestEventManager:
    """Test the event manager functionality."""

    def test_enque_event(self, event_manager):
        """Check if the number of events increases if an event is enqueued."""
        qsize_before = event_manager.events.qsize()
        event_manager.enqueue_event(Event())
        qsize_after = event_manager.events.qsize()

        assert qsize_after == qsize_before + 1

    def test_register_listener(self, event_manager, entity_manager):
        """Test the enlistment of one or more processors for a specific event
        type."""
        event_type = "TestRegister"
        processor = EventProcessor(event_manager, entity_manager)
        processor2 = EventProcessor(event_manager, entity_manager)
        event_manager.register_listener(event_type, processor)
        assert event_type in event_manager.listeners
        assert event_manager.listeners[event_type] == [processor]
        event_manager.register_listener(event_type, processor2)
        assert event_type in event_manager.listeners
        assert event_manager.listeners[event_type] == [processor, processor2]

    def test_remove_listener(self, event_manager, entity_manager):
        """Checks if a processor can be unregistered."""
        event_type = "TestUnregister"
        processor = EventProcessor(event_manager, entity_manager)
        processor2 = EventProcessor(event_manager, entity_manager)
        event_manager.listeners.update({event_type: [processor, processor2]})
        event_manager.remove_listener(event_type, processor)
        assert event_manager.listeners[event_type] == [processor2]
        event_manager.remove_listener(event_type, processor2)
        assert event_manager.listeners[event_type] == []

    def test_process_events(self, event_manager, entity_manager):
        """Checks if the events in the queue are processed"""
        event = Event()
        event2 = Event()
        event_type = event.type()
        processor = EventProcessor(event_manager, entity_manager)
        event_manager.listeners.update({event_type: [processor]})
        event_manager.events.put(event)
        event_manager.events.put(event2)
        assert event_manager.process_events(1) > 0
        assert event_manager.events.empty()
