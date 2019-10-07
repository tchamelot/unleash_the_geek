import sys


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
    map = [[('?', '0')] * width] * height
    entities = dict()
    allies = set()
    ores = []

    while True:
        # Get the score
        scores = [int(i) for i in input().split()]

        # Get the map
        for i in range(height):
            inputs = input().split()
            for j in range(width):
                state = (inputs[2*j], inputs[2*j+1])
                if state[0] not in ['?', '0']:
                    ores.append((j, i))
                map[i][j] = state

        # Get entity
        entity_count, radar_cd, trap_cd = [int(i) for i in input().split()]
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
