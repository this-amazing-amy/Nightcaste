from pygame import Rect


class QTreeCollisionManager:

    def fill(self, bounds, collidables):
        """Add all collidable objects to a quad tree. O(n * log n)"""
        self.qtree = QuadTree(bounds)
        for entity, collidable in collidables.iteritems():
            self.qtree.insert(entity, collidable)

    def move(self, entity):
        """Notifies the collision manager that an entits rect was moved. The
        entity will be relocated in the quad tree.

        NOTE: The methods assumes the entites rect was moved in place!"""
        self.qtree.move(entity)

    def collide_rect(self, entity, rect):
        collisions = self.qtree.retrieve(rect)
        try:
            collisions.remove(entity)
        except ValueError:
            pass
        return collisions


class QuadTreeObject:

    def __init__(self, rect):
        self.rect = rect
        self.owner = None


class QuadTree:

    def __init__(self, bounds, max_entites=5, max_level=5):
        self.entites = {}
        self.q_tree_root = QuadTreeNode(None, 0, bounds, max_entites, max_level)

    def bounds(self):
        return self.q_tree_root.bounds

    def get_all(self):
        return self.entites.viewkeys()

    def contains(self, entity):
        return entity in self.entites

    def count(self):
        return len(self.entites)

    def retrieve(self, rect):
        colliding_entities = []
        self.q_tree_root.retrieve(rect, colliding_entities)
        return colliding_entities

    def insert(self, entity, rect):
        q_tree_object = QuadTreeObject(rect)
        self.entites[entity] = q_tree_object
        self.q_tree_root.insert(entity, q_tree_object)

    def remove(self, entity):
        if self.contains(entity):
            self.q_tree_root.delete(entity, self.entites.pop(entity))
            return True
        return False

    def move(self, entity):
        if self.contains(entity):
            self.q_tree_root.move(entity, self.entites[entity])
            return True
        return False


class QuadTreeNode:
    """Implements a static QuadTree for collision detection."""

    def __init__(self, parent, level, bounds, max_entites=5, max_level=5):
        self.parent = None
        self.level = level
        self.bounds = bounds
        self.max_entities = max_entites
        self.max_level = max_level
        self.entites = {}
        self.nodes = None

    def split(self):
        """Splits the node into 4 subnodes."""
        sub_w = int(self.bounds.w / 2)
        sub_h = int(self.bounds.h / 2)
        x = self.bounds.x
        y = self.bounds.y

        self.nodes = [
            QuadTreeNode(
                self,
                self.level + 1,
                Rect(x + sub_w, y, sub_w, sub_h),
                self.max_entities,
                self.max_level),
            QuadTreeNode(
                self,
                self.level + 1,
                Rect(x, y, sub_w, sub_h),
                self.max_entities,
                self.max_level),
            QuadTreeNode(
                self,
                self.level + 1,
                Rect(x, y + sub_h, sub_w, sub_h),
                self.max_entities,
                self.max_level),
            QuadTreeNode(
                self,
                self.level + 1,
                Rect(x + sub_w, y + sub_h, sub_w, sub_h),
                self.max_entities,
                self.max_level)]
        self._distribute()

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

    def insert(self, entity, item):
        """Insert the object into the quadtree. If the node exceeds the
        capacity, it will split and add all objects to their corresponding
        nodes."""
        if self.nodes is not None:
            index = self._get_index(item.rect)
            if index != -1:
                self.nodes[index].insert(entity, item)
                return

        self.entites[entity] = item
        item.owner = self
        if len(self.entites) > self.max_entities and self.level < self.max_level:
            if self.nodes is None:
                self.split()

    def _distribute(self):
        """Checks of the entites in this node fits into a subnode and inserts
        it."""
        # Do not copy any items since the refenrences to the orignal rects must
        # stay valid for move/relocate
        for entity in self.entites.keys():
            index = self._get_index(self.entites[entity].rect)
            if index != -1:
                self.nodes[index].insert(entity, self.entites.pop(entity))

    def retrieve(self, rect, result):
        """Fills the given list with all objects that collide with the given
        rect."""
        if self.nodes is not None:
            index = self._get_index(rect)
            if index != -1:
                self.nodes[index].retrieve(rect, result)
        for entity, item in self.entites.iteritems():
            if rect.colliderect(item.rect):
                result.append(entity)

    def delete(self, entity, item, clean=True):
        """Removes an item from its node."""
        if item.owner is not None:
            if item.owner == self:
                del self.entites[entity]
                if clean:
                    self._clean_upwards()
            else:
                item.owner.delete(entity, item)

    def move(self, entity, item):
        """Calls _relacote on the items current node."""
        if item.owner is not None:
            item.owner._relocate(entity, item)

    def _relocate(self, entity, item):
        """Moves an item with the tree. If the item doesn't fit into this leaf
        anymore, the call will be delegated to the parent."""
        # do we fit into this node
        if (self.bounds.contains(item.rect)):
            # do we fit into our childs
            if self.nodes is not None:
                index = self._get_index(item.rect)
                if index != -1:
                    dest = self.nodes[index]
                    if item.owner != dest:
                        # remove from old node and add to our child
                        former_owner = item.owner
                        # delay cleanup since it could delete our destination
                        self.delete(entity, item, False)
                        dest.insert(entity, item)
                        # delyed cleanup
                        former_owner._clean_upwards()
        elif self.parent is not None:
            self.parent._relocate(item)

    def _clean_upwards(self):
        """Checks if the childs are empty and deletes them. If this Node is
        empty, the call will be delegated to the parent."""
        if self.nodes is not None:
            all_empty = True
            for node in self.nodes:
                all_empty &= node.is_empty()
            if all_empty:
                self.nodes = None
        if self.parent is not None and self.is_empty:
            self.parent._clean_upward()

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

    def is_empty(self):
        return self.count() == 0

    def __str__(self):
        return 'QuadTreeNode(level: %d, bounds: %s, entities: %d)'  % (
            self.level, self.bounds, len(self.entites))
