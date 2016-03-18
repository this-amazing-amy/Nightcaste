""" Map generation tool for creating random maps, based on BSP-Trees """

from entities import EntityConfiguration
import random
import math
import logging
import tcod as libtcod


class MapManager():
    """ The Map Manager stores and administrates all maps
    It holds generators for different types of maps """

    def __init__(self, entity_manager):
        self.entity_manager = entity_manager
        self.maps = {}
        self.generators = {'dungeon': DungeonGenerator(self.entity_manager),
                           'world': WorldspaceGenerator(self.entity_manager)}

    def get_map(self, name=None, level=0, type="dungeon"):
        if name is None:
            name = self.random_name()
        collection = self.get_mapcollection(name)
        if (len(collection) > level):
            return collection[level]
        else:
            return self.generators[type].generate_map(name, level)

    def get_mapcollection(self, name):
        if self.maps.get(name, None) is None:
            self.maps[name] = []
        return self.maps[name]

    def random_name(self):
        # TODO: Implement random dungeon name generation
        return "Random Dungeon"


class MapGenerator():
    """Generates maps and returns the id of the generated map """
    logger = logging.getLogger('mapcreation.MapGenerator')

    def __init__(self, entity_manager):
        self.entity_manager = entity_manager
        self.tiles = []
        # TODO: Get tileset size from config
        self.tilesetsize = 32

    def create_empty_map(self, width, height, tile="stone_wall"):
        """ Returns a new Tile array with set size filled with walls"""

        self.logger.debug("Map size: %sx%s", width, height)
        return [[self.create_tile(tile, x, y)
                 for y in range(0, height)]
                for x in range(0, width)]

    def create_tile(self, blueprint, x, y):
        """ Creates a tile from the specified blueprint name """
        tile = self.get_tile(x, y)
        if tile is not None:
            self.entity_manager.destroy_entity(self.get_tile(x, y))
        tile_config = EntityConfiguration()
        tile_config.add_attribute('Position', 'x', x * self.tilesetsize)
        tile_config.add_attribute('Position', 'y', y * self.tilesetsize)
        tile = self.entity_manager.new_from_blueprint_and_config(
            "tiles." + blueprint, tile_config)
        tileComp = (self.entity_manager.get(tile, "Tile"))
        if (tileComp.variant):
            tileComp.name += "_" + str(random.sample(tileComp.variant, 1)[0])
        return tile

    def create_custom_tile(self, x, y, char, colliding):
        """Creates a tile with the specified properties."""
        tile_config = EntityConfiguration()
        tile_config.add_attribute('Position', 'x', x * self.tilesetsize)
        tile_config.add_attribute('Position', 'y', y * self.tilesetsize)
        tile_config.add_attribute('Renderable', 'character', char)
        tile_config.add_attribute('Colliding', 'active', colliding)
        return self.entity_manager.new_from_config(tile_config)

    def is_blocked(self, x, y):
        """ Returns True, if the given position on the map has an enabled
        Colliding component """
        colliding = self.entity_manager.get(self.get_tile(x, y), 'Colliding')
        return (colliding is not None and colliding.active)

    def get_tile(self, x, y):
        """ Returns the bottommost entity at the given position """
        if len(self.tiles) > x and len(self.tiles[x]) > y:
            return self.tiles[x][y]
        return None

    def create_stairs(self, x, y, target_map=None, target_level=None):
        """ Creates a stair entity at the given position leading to the given
        map and level """
        tile = self.create_tile("stairs", x, y)
        self.entity_manager.set_entity_attribute(tile, "MapTransition",
                                                 'target_map', target_map)
        self.entity_manager.set_entity_attribute(tile, "MapTransition",
                                                 'target_level', target_level)
        return tile


class WorldspaceGenerator(MapGenerator):
    """ Loads the worldspace or generates it from scratch """

    def generate_map(self, map_name, level):
        height = 100
        width = 140

        height = random.randrange(math.floor(height * 0.7), height)
        width = random.randrange(math.floor(width * 0.7), width)

        self.tiles = self.create_empty_map(width, height, "stone_floor")
        # TODO: Make Spawn Routine
        self.tiles[25][25] = self.create_stairs(25, 25)

        map_config = EntityConfiguration()
        map_config.add_attribute('Map', 'name', map_name)
        map_config.add_attribute('Map', 'tiles', self.tiles)
        map_config.add_attribute('Map', 'level', level)
        map_config.add_attribute('Map', 'entry', (20, 20))
        map_config.add_attribute('Map', 'tilesetsize', self.tilesetsize)
        return self.entity_manager.new_from_config(map_config)


class DungeonGenerator(MapGenerator):
    """The Map Generator can generate predefined or random maps.

    Args:
        tiles [(int)]: Two-dimensional array of tiles created
        rooms [(Room)]: Array of all rooms created during traversion

    """
    logger = logging.getLogger('mapcreation.DungeonGenerator')

    def generate_map(self, map_name, level):
        """Loads the map configuration based on map name and level and generates
        the new map.

        Args:
            map_name (str): The name of the map to generate.
            level (int): The level of the map.

        """
        height = 100
        width = 140

        height = random.randrange(math.floor(height * 0.7), height)
        width = random.randrange(math.floor(width * 0.7), width)

        self.rooms = []
        self.tiles = self.create_empty_map(width, height)
        tree = self.create_bsp_tree(width, height)
        self.traverse_tree(tree, self.process_node)

        map_config = EntityConfiguration()
        map_config.add_attribute('Map', 'name', map_name)
        map_config.add_attribute('Map', 'tiles', self.tiles)
        map_config.add_attribute('Map', 'level', level)
        map_config.add_attribute('Map', 'tilesetsize', self.tilesetsize)
        entry = random.sample(self.rooms, 1)[0].random_spot()
        map_config.add_attribute('Map', 'entry', entry)
        return self.entity_manager.new_from_config(map_config)

    def process_node(self, node, userData=0):
        """ Processes the given node, create room if it is a leaf
            or connect child nodes with a corridor if not """
        if libtcod.bsp_is_leaf(node):
            self.create_room(node)
        else:
            self.create_corridor(node)
        return True

    def create_room(self, node):
        """ Creates a randomly-sized room inside the given node.
        appends the Room-object onto the rooms-list of the map """
        width = random.randrange(node.w / 2, node.w)
        height = random.randrange(node.h / 2, node.h)
        room = Room(node.x, node.y, width, height)
        for x in range(room.x + 1, room.x + width + 1):
            for y in range(room.y + 1, room.y + height + 1):
                self.tiles[x][y] = self.create_tile("stone_floor", x, y)
        self.logger.debug(
            "Created room on %s,%s sized %sx%s",
            node.x,
            node.y,
            width,
            height)
        self.rooms.append(room)

    def random_spot_in_node(self, node):
        x = random.randrange(node.x, node.x + node.w - 1)
        y = random.randrange(node.y, node.y + node.h - 1)
        while (self.is_blocked(x, y)):
            x = random.randrange(node.x, node.x + node.w - 1)
            y = random.randrange(node.y, node.y + node.h - 1)
        return (x, y)

    def create_corridor(self, node):
        """ Creates a corridor between random spots in two nodes"""
        (x1, y1) = self.random_spot_in_node(self.left_child(node))
        (x2, y2) = self.random_spot_in_node(self.right_child(node))
        self.logger.info(
            "Generating Corridor between %s and %s", (x1, y1), (x2, y2))
        if (random.randrange(2) == 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.tiles[x1][y] = self.create_tile("stone_floor", x1, y)
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.tiles[x][y2] = self.create_tile("stone_floor", x, y2)
        else:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.tiles[x][y1] = self.create_tile("stone_floor", x, y1)
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.tiles[x2][y] = self.create_tile("stone_floor", x2, y)

    def left_child(self, node):
        """ Returns the left child of the given node"""
        return libtcod.bsp_left(node)

    def right_child(self, node):
        """ Returns the right child of the given node"""
        return libtcod.bsp_right(node)

    def traverse_tree(self, tree, callback):
        """ Apply the given function to every node of the tree """
        libtcod.bsp_traverse_post_order(tree, callback, 0)

    def create_bsp_tree(self, width, height):
        """ Returns a new BSP tree, wrapping the libtcod bsp toolkit """
        tree = libtcod.bsp_new_with_size(0, 0, width - 2, height - 2)
        libtcod.bsp_split_recursive(tree, 0, 6, 8, 8, 1.3, 1.3)
        return tree


class Room():

    """A room on the map, connected with each other through corridors

        Args:
            x (int): horizontal position of upper left corner
            y (int): vertical position of upper left corner
            width (int)
            height (int)
    """

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def random_spot(self):
        return (random.randint(self.x, self.x + self.width),
                random.randint(self.y, self.y + self.height))
