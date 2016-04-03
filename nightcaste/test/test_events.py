"""Tests events. Propably not mutch to do here since events are mostly simple
data transfer objects"""
import pytest
from nightcaste.entities import EntityManager
from nightcaste.events import Event
from nightcaste.events import EventManager
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
        event = Event("Event")
        assert event.identifier == 'Event'


class TestEventManager:
    """Test the event manager functionality."""

    def test_enque_event(self, event_manager):
        """Check if the number of events increases if an event is enqueued."""
        qsize_before = event_manager.events.qsize()
        event_manager.throw_new('Event')
        qsize_after = event_manager.events.qsize()

        assert qsize_after == qsize_before + 1

    def test_register_listener(self, event_manager, entity_manager):
        """Test the enlistment of one or more processors for a specific event
        type."""
        event_type = "TestRegister"
        processor_function = self.on_test_event
        processor_function2 = self.on_test_event2
        event_manager.register_listener(event_type, processor_function)
        assert event_type in event_manager.listeners
        assert event_manager.listeners[event_type] == [processor_function]
        event_manager.register_listener(event_type, processor_function2)
        assert event_type in event_manager.listeners
        assert event_manager.listeners[event_type] == [
            processor_function, processor_function2]

    def on_test_event(self, event):
        pass

    def on_test_event2(self, event):
        pass

    def test_remove_listener(self, event_manager, entity_manager):
        """Checks if a processor can be unregistered."""
        event_type = "TestUnregister"
        processor = self.on_test_event
        processor2 = self.on_test_event2
        event_manager.register_listener(event_type, processor)
        event_manager.register_listener(event_type, processor2)
        assert event_manager.listeners[event_type] == [processor, processor2]
        event_manager.remove_listener(event_type, processor)
        assert event_manager.listeners[event_type] == [processor2]
        event_manager.remove_listener(event_type, processor2)
        assert event_manager.listeners[event_type] == []

    def test_process_events(self, event_manager, entity_manager):
        """Checks if the events in the queue are processed"""
        event_type = 'TestProcess'
        event_manager.register_listener(event_type, self.on_test_event)
        event_manager.throw_new(event_type)
        event_manager.throw_new(event_type)
        assert event_manager.process_events() > 0
        assert event_manager.events.empty()
