import sys
import numpy as np
from enum import IntEnum


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
    class Task(IntEnum):
        AVAILABLE = 0
        PLACE_RADAR = 1
        RADAR = 2
        DEAD = 3

    def __init__(self, x, y, item):
        super().__init__(x, y, item)
        self.action = 'WAIT'
        self.task = Robot.Task.AVAILABLE

    def update(self, x, y, item):
        super().update(x, y, item)
        if (x < 0) or (y < 0):
            self.task = Robot.Task.DEAD

    def radar(self):
        if self.task == Robot.Task.RADAR:
            self.action = 'REQUEST RADAR'
            if self.item == 2:
                self.task = Robot.Task.PLACE_RADAR
        if self.task == Robot.Task.PLACE_RADAR:
            self.action = 'DIG %s %s' % self.target
            if self.item != 2:
                self.task = Robot.Task.AVAILABLE
                self.action = 'WAIT'

        self.action += ' RADAR'

    def play(self):
        """
        Output the robot action for the current round
        """
        if self.task == Robot.Task.AVAILABLE:
            self.action = 'WAIT'
        elif self.task <= Robot.Task.RADAR:
            self.radar()
        if self.task == Robot.Task.DEAD:
            self.action = 'WAIT DEAD'

        print(self.action)

    def get_task(self, task, target):
        self.task = task
        self.target = target


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
        self.radar = Radar(5, 5, -1)
        self.radar_busy = False

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


class Supervizor:
    def __init__(self):
        self.tasks = []
        pass

    def create_task(self, env):
        self.tasks = []

        # Handle Radar
        if env.radar_cd == 0 and not env.radar_busy:
            env.radar_busy = True
            self.tasks.append((Robot.Task.RADAR, (env.radar.x, env.radar.y)))
            env.radar.x = (env.radar.x + 4) % env.width
            env.radar.y = (env.radar.y + 4) % env.height
        elif env.radar_cd != 0:
            env.radar_busy = False

    def assign_tasks(self, env):
        for ally in env.allies:
            unit = env.entities[ally]
            if unit.task == Robot.Task.AVAILABLE:
                try:
                    # Decompose tuple in multiple args
                    unit.get_task(*self.tasks.pop())
                except IndexError:
                    pass
            unit.play()


def main():

    env = Environment()
    supervizor = Supervizor()

    while True:

        env.parse()

        supervizor.create_task(env)
        supervizor.assign_tasks(env)


if __name__ == '__main__':
    sys.exit(main())
