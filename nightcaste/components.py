"""This module contains all nightcaste components. A component describes a
specific property or a set of proerties in order to represent certain ability or
property of an entity. The entity itself is only a composition of its
components."""


class Component:
    """The base class of every component."""

    def type(self):
        """Returns the class name of the component."""
        return self.__class__.__name__

    def __str__(self):
        result = self.type()+" ("
        for prop, val in self.__dict__.iteritems():
            result += str(prop)+": "+str(val)+", "
        return result[:-2] + ")"


class Position(Component):
    """Represents a position on a plane.

    Args:
        x (int): Horizontal position.
        y (int): Vertical position.

    """

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


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


class Colliding(Component):
    """ Anything that can collide with each other """

    def __init__(self, active=True):
        self.active = active


class Color(Component):
    """Represents an entity with a color.

    Args:
        r (int): Red fraction of the color.
        g (int): Green fraction of the color.
        b (int): Blue fraction of the color.

    """

    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b


class InputComponent(Component):
    """Entity which are receiving input. (WIP Currently Empty will contain e.g
    MoveDirection)"""
    pass


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
                 children=[], entry=None):
        self.name = name
        self.level = level
        self.parent = parent
        self.tiles = tiles
        self.entry = entry
        self.children = children

    def width(self):
        return len(self.tiles)

    def height(self):
        return len(self.tiles[0])

    def get_entites_in_frame(self, x, y, width, height):
        return [map_column[y:y+height] for map_column in self.tiles[x:x+width]]

    def add_child(self, child):
        """Added a child to the list of know child maps.

        Args:
            child (object): The child entity to add.

        """
        self.children.append(child)


class MapTransition(Component):
    """ A map piece that can transport entities to other maps

    Args:
        target_map: The map the transition leads to
        target_level: The level numver the transition leads to
    """
    def __init__(self, target_map=None, target_level=None):
        self.target_map = target_map
        self.target_level = target_level


class Useable(Component):
    """ An entity that can be used (eg doors, stairs, chests, etc.)
    On use, its useEvent will be called with the entity's id as a parameter

    Args:
        useEvent (str): Identifier for the event that will be thrown on use
    """

    def __init__(self, useEvent=None):
        self.useEvent = useEvent
