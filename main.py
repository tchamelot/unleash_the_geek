import sys
from enum import IntEnum
from collections import deque
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
    class Task(IntEnum):
        AVAILABLE = 0
        PLACE_RADAR = 1
        RADAR = 2
        BASE = 3
        ORE = 4
        DEAD = 100

    def __init__(self, x, y, item):
        super().__init__(x, y, item)
        self.action = 'WAIT'
        self.task = Robot.Task.AVAILABLE
        self.target = (0, 0)

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

    def ore(self):
        if self.task == Robot.Task.ORE:
            self.action = 'DIG %s %s' % self.target
            if self.item == 4:
                self.task = Robot.Task.BASE
        if self.task == Robot.Task.BASE:
            self.action = 'MOVE 0 %s' % self.y
            if self.item != 4:
                self.task = Robot.Task.AVAILABLE
                self.action = 'WAIT'

        self.action += ' ORE'

    def play(self):
        """
        Output the robot action for the current round
        """
        if self.task == Robot.Task.AVAILABLE:
            self.action = 'WAIT'
        elif self.task <= Robot.Task.RADAR:
            self.radar()
        elif self.task <= Robot.Task.ORE:
            self.ore()
        elif self.task == Robot.Task.DEAD:
            self.action = 'WAIT DEAD'

        print(self.action)

    def get_task(self, task, target):
        self.task = task
        self.target = target


class Radar(Entity):
    """
    Entity that shows ore lodesa nd enemy traps
    """


class Trap(Entity):
    """
    Entity that shows ore lodesa nd enemy traps
    """


ENTITY_FACTORY = {
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
        self.radars = set()
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
            u_id, unit_type, x, y, item = [int(j) for j in input().split()]
            try:
                self.entities[u_id].update(x, y, item)
            except KeyError:
                self.entities[u_id] = ENTITY_FACTORY[unit_type](x, y, item)
            if unit_type == 0:
                self.allies.add(u_id)
            if unit_type == 1:
                self.enemies.add(u_id)
            if unit_type == 2:
                self.radars.add(u_id)

    def ore_count(self):
        return self.ore[self.ore > 0].sum()

    def surface_coverd_by_radar(self):
        return len(self.ore[self.ore >= 0])


class Supervizor:
    def __init__(self):
        self.tasks = deque()
        self.desired_radar_poses = {(24, 12), (24, 4), (22, 8), (18, 4), (18, 12), (14, 8), (9, 4), (9, 12), (5, 8)}

    def create_task(self, env):
        self.tasks = deque()
        # Handle Radar
        actual_radar_pose = {
            env.entities[id_radar].get_loc()
            for id_radar in env.radars
        }
        remaining_radar_poses = (self.desired_radar_poses - actual_radar_pose)
        if (env.radar_cd == 0) and len(remaining_radar_poses) != 0:
            pose = remaining_radar_poses.pop()
            # for pose in (self.desired_radar_poses - actual_radar_pose):
            self.tasks.append((Robot.Task.RADAR, pose))
            env.radar_cd = 5

        # Handle ore
        for i, column in enumerate(env.ore.T):
            for j, ore in enumerate(column):
                if ore > 0:
                    self.tasks.extendleft(
                        [(Robot.Task.ORE, (i, j))] * ore
                    )

        print(self.tasks, file=sys.stderr)

    def assign_tasks(self, env):
        for ally in env.allies:
            unit = env.entities[ally]
            if (unit.task != Robot.Task.AVAILABLE) or (unit.task != Robot.Task.ORE):
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
