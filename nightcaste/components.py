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
        return '%s(%d, %d)' % (self.type(), self.x, self.y)


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
            self.type(), self.character, self.z_index, self.visible)


class Colliding(Component):
    """ Anything that can collide with each other """

    def __init__(self, blocking=True):
        self.blocking = blocking

    def __str__(self):
        return '%s(%s)' % (self.type(), self.blocking)


class Color(Component):
    """Represents an entity with a color.
    TODO: Merge with Renderable?

    Args:
        r (int): Red fraction of the color.
        g (int): Green fraction of the color.
        b (int): Blue fraction of the color.

    """

    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return 'Color(%d, %d, %d)' % (self.r, self.g, self.b)


class Map(Component):
    """A contains a 2 dimensional array referancing the tile entities. A map can
    reference one parent and many childs for map navigation.

    Args:
        name (str): The name of the map.
        level (int): How deep in the map tree.
        parent (object): The parent entity.
        tiles ([[object]]): 2-dimensional array with tile entities.
        children ([object]): List with child entities.

    """

    def __init__(self, name=None, level=0, parent=None, tiles=None,
                 children=[]):
        self.name = name
        self.level = level
        self.parent = parent
        self.tiles = tiles
        self.children = children

    def __str__(self):
        return 'Map("%s", level %d)' % (self.name, self.level)

    def add_child(self, child):
        """Added a child to the list of know child maps.

        Args:
            child (object): The child entity to add.

        """
        self.children.append(child)
