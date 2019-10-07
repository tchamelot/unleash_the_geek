import sys
import numpy as np

class Entity:
    """
    Base class for entity on the map
    """

    def __init__(self, x, y, item):
        """
        Create a new entity at ```x```, ```y``` with ```item```
        """
        self.x = x
        self.y = y
        self.item = item

    def update(self, x, y, item):
        """
        Update an entity without calling the constructor again
        """
        self.x = x
        self.y = y
        self.item = item


class Robot(Entity):
    """
    Entity that will seek for amadeusium
    """

    def __init__(self, x, y, item):
        super().__init__(x, y, item)
        self.action = 'WAIT'

    def update(self, x, y, item):
        super().update(x, y, item)

    def play(self):
        print(self.action)


class Radar(Entity):
    """
    Entity that shows ore lodesa nd enemy traps
    """

    def __init__(self, x, y, item):
        super().__init__(x, y, item)


class Trap(Entity):
    """
    Entity that shows ore lodesa nd enemy traps
    """

    def __init__(self, x, y, item):
        super().__init__(x, y, item)


entity_factory = {
    0: Robot,
    1: Robot,
    2: Radar,
    3: Trap,
    }


def main():

    # Get map dimensions
    width, height = [int(i) for i in input().split()]
    ore = np.zeros((height, width), dtype=np.int8)
    hole = np.zeros((height, width), dtype=np.bool)
    entities = dict()
    entity_count, radar_cd, trap_cd = 0, 0, 0
    allies = set()

    while True:
        # Get the score
        myScore, enemyScore = [int(i) for i in input().split()]

        # Get the map
        for i in range(height):
            row = np.vectorize(np.uint8)\
                (
                    input().replace('?', '-1')  # replace ? in the string
                        .split()  # convert to to array
                )  # convert this to int
            ore[i, :] = row[0::2]  # 1 over 2 element starting at 0
            hole[i, :] = row[1::2]  # 1 over 2 elements starting at 1

        # Get entity
        entity_count, radar_cd, trap_cd = np.vectorize(np.uint8)(input().split())
        for i in range(entity_count):
            id, type, x, y, item = [int(j) for j in input().split()]
            try:
                entities[id].update(x, y, item)
            except KeyError:
                entities[id] = entity_factory[type](x, y, item)
            if type == 0:
                allies.add(id)

        # AI here

        for ally in allies:
            unit = entities[ally]
            unit.play()


if __name__ == '__main__':
    sys.exit(main())
