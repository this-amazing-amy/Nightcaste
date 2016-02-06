"""This module contains all nightcaste components. A component describes a
specific property or a set of proerties in order to represent certain ability or
property of an entity. The entity itself is only a composition of its
components."""


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

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __str__(self):
        return '%s(%d, %d)' % (self.type, self.x, self.y)


class Renderable(Component):

    """Represents an entity that can be rendered

    Args:
        character (str): printed character
        z_index (int): Order to be printed (lowest first)
    """

    def __init__(self, character=None, z_index=0, visible=True):
        self.character = character
        self.z_index = z_index
        self.visible = True

    def __str__(self):
        return '%s(%s, %d, %s)' % (
            self.type, self.character, self.z_index, self.visible)
