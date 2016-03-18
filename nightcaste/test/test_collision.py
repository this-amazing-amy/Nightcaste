from pygame import Rect
from nightcaste.collision import QuadTree


class TestQuadTree:

    def test_insert(self):
        qtree = QuadTree(0, Rect(0, 0, 100, 100), 2, 2)
        assert qtree.height() == 0
        assert qtree.count() == 0

        qtree.insert(Rect(5, 5, 10, 10), 0)
        assert qtree.height() == 0
        assert qtree.count() == 1

        qtree.insert(Rect(80, 5, 10, 10), 1)
        assert qtree.height() == 0
        assert qtree.count() == 2

        qtree.insert(Rect(5, 80, 10, 10), 3)
        assert qtree.height() == 1
        assert qtree.count() == 3

        qtree.insert(Rect(35, 80, 10, 10), 4)
        assert qtree.height() == 1
        assert qtree.count() == 4

        qtree.insert(Rect(5, 80, 10, 10), 5)
        assert qtree.height() == 2
        assert qtree.count() == 5

    def test_retrieve(self):
        qtree = QuadTree(0, Rect(0, 0, 100, 100), 2, 2)
        qtree.insert(Rect(5, 5, 10, 10), 0)
        qtree.insert(Rect(80, 5, 10, 10), 1)
        qtree.insert(Rect(5, 80, 10, 10), 3)
        qtree.insert(Rect(35, 80, 10, 10), 4)
        qtree.insert(Rect(5, 80, 10, 10), 5)

        collidable = Rect(30, 82, 10, 10)
        collisions = {}
        qtree.retrieve(collisions, collidable)
        assert collisions == {4: Rect(35, 80, 10, 10)}
