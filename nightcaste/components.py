"""This module contains all nightcaste components. A component describes a
specific property or a set of proerties in order to represent certain ability or
property of an entity. The entity itself is only a composition of its
components."""


class ComponentManager:
    """ The Component manager stores the components for all entities (represented by
    int entity_id) """

    def __init__(self):
        # Two-dimensional dictionary holding the components of all entities
        # {component_type: {entity_id: Component}}
        self.components = {}

    def add_component(self, entity_id, component):
        component_type = component.type()
        component_dict = self.components.get(component_type, {})
        if (component_dict is not None):
            component_dict = {}
            self.components[component_type] = component_dict
        self.components[component_type][entity_id] = component

    def remove_component(self, entity_id, component_type):
        pass

    def get_component(self, entity_id, component_type):
        pass

    def get_all_of_type(self, component_type):
        pass


class Component:
    """The base class of every component."""

    def type(self):
        """Returns the class name of the component."""
        return self.__class__.__name__


class Position(Component):
    """Represents a position on a plane.

    Args:
        x (int): Horizontal position.
        y (int): Vertical position.

    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
