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

    def get_loc(self):
        return self.x, self.y

    def dist_with(self, x, y):
        return abs(self.x-x) + abs(self.y-y)


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


class Environment:

    def __init__(self):
        # Get map dimensions
        self.width, self.height = [int(i) for i in input().split()]
        self.my_score = 0
        self.enemy_score = 0
        self.ore = np.zeros((self.height, self.width), dtype=np.int8)
        self.hole = np.zeros((self.height, self.width), dtype=np.bool)
        self.entities = dict()
        self.entity_cnt = 0
        self.radar_cd = 0
        self.trap_cd = 0
        self.allies = set()
        self.enemies = set()

    def parse(self):
        # Get the score
        self.my_score, self.enemy_score = [int(i) for i in input().split()]
        # Get the map
        for i in range(self.height):
            row = np.vectorize(np.uint8)(
                    input().replace('?', '-1')  # replace ? in the string
                        .split()  # convert to to array
                )  # convert this to int
            self.ore[i, :] = row[0::2]  # 1 over 2 element starting at 0
            self.hole[i, :] = row[1::2]  # 1 over 2 elements starting at 1
        # Get entities
        self.entity_cnt, self.radar_cd, self.trap_cd = np.vectorize(np.uint8)(
            input().split()
            )
        for i in range(self.entity_cnt):
            id, type, x, y, item = [int(j) for j in input().split()]
            try:
                self.entities[id].update(x, y, item)
            except KeyError:
                self.entities[id] = entity_factory[type](x, y, item)
            if type == 0:
                self.allies.add(id)
            if type == 1:
                self.enemies.add(id)

    def ore_count(self):
        return self.ore[self.ore > 0].sum()

    def surface_coverd_by_radar(self):
        return len(self.ore[self.ore >= 0])


def main():

    env = Environment()

    while True:

        env.parse()

        for ally in env.allies:
            unit = env.entities[ally]
            unit.play()


if __name__ == '__main__':
    sys.exit(main())
