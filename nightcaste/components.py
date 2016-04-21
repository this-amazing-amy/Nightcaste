"""This module contains all nightcaste components. A component describes a
specific property or a set of proerties in order to represent certain ability or
property of an entity. The entity itself is only a composition of its
components."""
from pygame.sprite import DirtySprite
from pygame import Rect


class Component:
    """The base class of every component."""

    def type(self):
        """Returns the class name of the component."""
        return self.__class__.__name__

    def __str__(self):
        result = self.type() + " ("
        for prop, val in self.__dict__.iteritems():
            result += str(prop) + ": " + str(val) + ", "
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
        self.x_frac = x
        self.y_frac = y

    def move(self, dx, dy):
        self.x_frac += dx
        self.y_frac += dy
        self.x = int(self.x_frac)
        self.y = int(self.y_frac)


class Movement(Component):
    """ Holds the movement speed of an entity
    Args:
        speed (int): Movement Speed
    """

    def __init__(self, speed=8):
        # TODO: Scale correctly to have m/s
        self.speed = speed


class Direction():

    D_UP = 1
    D_DOWN = 2
    D_LEFT = 4
    D_RIGHT = 8

    def __init__(self, direction=0):
        self.direction = direction

    def set(self, direction=None, value=True):
        if value:
            self.direction |= direction
        else:
            self.direction &= ~direction

    def isset(self, direction):
        return (direction & self.direction) == direction

    def get_dx(self, distance):
        dx = 0
        if self.isset(self.D_LEFT):
            dx -= distance
        if self.isset(self.D_RIGHT):
            dx += distance
        return dx

    def get_dy(self, distance):
        dy = 0
        if self.isset(self.D_UP):
            dy -= distance
        if self.isset(self.D_DOWN):
            dy += distance
        return dy


class Renderable(Component):
    """Represents an entity that can be rendered

    Args:
        name (str): Identifies the renderable (usually used to reference an
            image over a config file)
        z_index (int): Order to be printed (lowest first)
        visible (boolean): Specifies wether this entity should be ignored from
        the renderer
    """

    def __init__(self, name=None, z_index=0, visible=True):
        self.name = name
        self.z_index = z_index
        self.visible = True


class Sprite(Renderable, DirtySprite):
    """Represents sprite in a 2D game.
    Args:
        x_offset/y_offset (float): Additional offset position, where the
            sprite should be rendered (to make animations between tiles
            possible
    """

    def __init__(self, sprite_name=None, anchor=(0, 0),
                 z_index=0, visible=True):
        DirtySprite.__init__(self)
        Renderable.__init__(self, sprite_name, z_index, visible)
        self.anchor = anchor
        self.animations = {}
        self.animation = None

    def add_animation(self, name, animation):
        self.animations[name] = animation

    def animate(self, animation_name):
        self.animation = self.animations[animation_name]

    def update(self, *args):
        if self.animation is not None:
            frame = self.animation.next_frame()
            if frame is not None:
                self.image = frame
                self.dirty = 1


class Animation:

    def __init__(self):
        self.frames = []
        self.current_frame = 0

    def add_frame(self, frame, ticks):
        for i in range(0, ticks):
            if i == 0:
                self.frames.append(frame)
            else:
                self.frames.append(None)

    def next_frame(self):
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return frame


class Turn(Component):
    """ An entity that participates in the turn logic, meaning
        it has an associated turn based behaviour

        Args:
            ticks: ticks since last action, the lower, the sooner it can act
            locking: boolean, if the game should wait for this entity's
                     behaviour to act, before others are handled
            min_turn_time: the real time that has to pass before this entity
                           behaviour can act again
            delta: real time that has passed before the last action
                   used to test for min_turn_time"""

    def __init__(self, ticks=0, locking=False, min_turn_time=0):
        self.ticks = ticks
        self.locking = locking
        # TODISCUSS: min_turn_time could also be in the inputBehaviour
        self.min_turn_time = min_turn_time
        self.delta = 0


class Tile(Renderable):
    """Represents a part of a background image / map in a 2D tile based game.
        offset: The vertical offset in which the Tile will be rendered.
                Negative values mean a multiple of the tilesetSize
                so -1 is good for walls etc.
    """

    def __init__(self, name=None, z_index=0, visible=True, variant=False,
                 offset=0):
        Renderable.__init__(self, name, z_index, visible)
        self.variant = variant
        self.offset = offset


class Colliding(Component, Rect):
    """ Anything that can collide with each other """

    def __init__(self, blocking=True, offset=(0, 0)):
        self.blocking = blocking
        self.offset = offset

    def set_position(self, x, y):
        self.x = x + self.offset[0]
        self.y = y + self.offset[1]


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


class Input(Component):
    """Entity which are receiving input."""

    def __init__(self, direction=Direction()):
        self.direction = direction


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
        return len(self.tiles) * self.tilesetsize

    def height(self):
        return len(self.tiles[0]) * self.tilesetsize

    def get_entites_in_frame(self, x, y, width, height):
        return [map_column[y:y + height]
                for map_column in self.tiles[x:x + width]]

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
