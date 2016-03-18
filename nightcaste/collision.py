from pygame import Rect


class QTreeCollisionManager:

    def update(self, bounds, collidables):
        """Add all collidable objects to a quad tree. O(n * log n)"""
        self.qtree = QuadTree(0, bounds)
        for entity, collidable in collidables.iteritem():
            self.qtree.insert(collidable, entity)

    def collide_rect(self, rect):
        collisions = []
        possible_collisions = {}
        self.qtree.retrieve(possible_collisions, rect)
        for entity, other_rect in possible_collisions.iteritems():
            if rect.colliderect(other_rect):
                collisions += entity
        return collisions


class QuadTree:
    """Implements a static QuadTree for collision detection."""

    def __init__(self, level, bounds, max_entites=5, max_level=5):
        self.level = level
        self.bounds = bounds
        self.max_entities = max_entites
        self.max_level = max_level
        self.entites = {}
        self.nodes = None

    def split(self):
        """Splits the node into 4 subnodes."""
        sub_w = (int)(self.bounds.w / 2)
        sub_h = (int)(self.bounds.h / 2)
        x = self.bounds.x
        y = self.bounds.y

        self.nodes = [
            QuadTree(
                self.level + 1,
                Rect(x + sub_w, y, sub_w, sub_h),
                self.max_entities,
                self.max_level),
            QuadTree(
                self.level + 1,
                Rect(x, y, sub_w, sub_h),
                self.max_entities,
                self.max_level),
            QuadTree(
                self.level + 1,
                Rect(x, y + sub_h, sub_w, sub_h),
                self.max_entities,
                self.max_level),
            QuadTree(
                self.level + 1,
                Rect(x + sub_w, y + sub_h, sub_w, sub_h),
                self.max_entities,
                self.max_level)]

    def _get_index(self, rect):
        """Determine which node the object belongs to. -1 means object cannot
        completely fit within a child node and is part of the parent node."""
        index = -1
        vertical_mid = self.bounds.x + (self.bounds.w / 2)
        horizontal_mid = self.bounds.y + (self.bounds.h / 2)

        # Object can completely fit within the top quadrants
        top = rect.y < horizontal_mid and rect.y + rect.h < horizontal_mid
        # Object can completely fit within the bottom quadrants
        bottom = rect.y > horizontal_mid

        # Object can completely fit within the left quadrants
        if rect.x < vertical_mid and rect.x + rect.w < vertical_mid:
            if top:
                index = 1
            elif bottom:
                index = 2
        # Object can completely fit within the right quadrants
        elif rect.x > vertical_mid:
            if top:
                index = 0
            elif bottom:
                index = 3

        return index

    def insert(self, rect, entity):
        """Insert the object into the quadtree. If the node exceeds the
        capacity, it will split and add all objects to their corresponding
        nodes."""
        if self.nodes is not None:
            index = self._get_index(rect)
            if index != -1:
                self.nodes[index].insert(rect, entity)
                return

        self.entites[entity] = rect
        if len(self.entites) > self.max_entities and self.level < self.max_level:
            if self.nodes is None:
                self.split()
            self.redistribute()

    def redistribute(self, deep=False):
        """Checks of the entites in this node fits into a subnode and inserts
        it.

        Args:
            deep (bool): If True calls redistribute on the whole subtree.
        """
        if deep and self.nodes is not None:
            for node in self.nodes:
                node.redistribute(deep)

        # TODO find better way than making a copy
        for entity, rect in self.entites.items():
            index = self._get_index(rect)
            if index != -1:
                del self.entites[entity]
                self.nodes[index].insert(rect, entity)

    def retrieve(self, entity_dict, rect):
        """Fills the given dict with all objects that could collide with the
        given object."""
        if self.nodes is not None:
            index = self._get_index(rect)
            if index != -1:
                self.nodes[index].retrieve(entity_dict, rect)
        entity_dict.update(self.entites)

    def height(self):
        """Calculate the height of the tree. The height is the maximum height of
        the child nodes + 1."""
        max = -1
        if self.nodes is not None:
            for node in self.nodes:
                height = node.height()
                max = height if height > max else max
        return max + 1

    def count(self):
        """Calculates the count of entites in the tree."""
        count = len(self.entites)
        if self.nodes is not None:
            for node in self.nodes:
                count += node.count()
        return count

    def __str__(self):
        return 'QuadTree(%s) height: %d count: %d' % (
            self.bounds, self.height(), self.count())
