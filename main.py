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
        return abs(self.x - x) + abs(self.y - y)


def dist(t1, t2):
    return abs(t1[0] - t2[0]) + abs(t1[1] - t2[0])


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
        self.assigned_task = Robot.Task.AVAILABLE
        self.target = (0, 0)

    def update(self, x, y, item):
        super().update(x, y, item)
        if (x < 0) or (y < 0):
            self.task = Robot.Task.DEAD
            self.assigned_task = Robot.Task.DEAD

    def radar(self, env):
        if self.task == Robot.Task.RADAR:
            self.action = 'REQUEST RADAR REQ_RADAR'
            env.radar_cd = 5
            if self.item == 2:
                self.task = Robot.Task.PLACE_RADAR
        if self.task == Robot.Task.PLACE_RADAR:
            self.action = 'DIG %s %s  DIG_RADAR' % self.target
            if self.item != 2:
                self.task = Robot.Task.AVAILABLE
                self.assigned_task = Robot.Task.AVAILABLE
                self.action = 'WAIT WAIT_RADAR'

    def ore(self, env):
        if self.task == Robot.Task.ORE:
            self.action = 'DIG %s %s DIG_ORE' % self.target
            if (self.x == 0) and (env.trap_cd == 0) and (self.item == -1):
                self.action = "REQUEST TRAP REQ_TRAP"
                env.trap_cd = 5
            else:
                # if (self.item == 3) and (self.dist_with(*self.target)<3):
                #     env.ally_traps[self.target[1], self.target[0]] = True
                #     # self.task = Robot.Task.BASE
                if self.item == 4:
                    self.task = Robot.Task.BASE
        if self.task == Robot.Task.BASE:
            self.action = 'MOVE 0 %s MOVE_ORE' % self.y
            if self.dist_with(*self.target) <= 1:
                env.ally_hole[self.target[1], self.target[0]] = True
            if self.item == -1:
                self.task = Robot.Task.AVAILABLE
                self.assigned_task = Robot.Task.AVAILABLE
                self.action = 'WAIT WAIT_ORE'

    def play(self, env):
        """
        Output the robot action for the current round
        """
        if self.task == Robot.Task.AVAILABLE:
            self.action = 'WAIT WAIT'
        elif self.task <= Robot.Task.RADAR:
            self.radar(env)
        elif self.task <= Robot.Task.ORE:
            self.ore(env)
        elif self.task == Robot.Task.DEAD:
            self.action = 'WAIT DEAD'

        self.action += "_%i_%i" % self.target

        print(self.action)

    def __str__(self):
        return "robot:\nloc:%i,%i\nstatus:%s task:%s" % (self.x, self.y, self.task.name, self.assigned_task.name)

    def get_task(self):
        return self.assigned_task, (self.target[0], self.target[1])

    def set_task(self, task, target):
        self.task = task
        self.assigned_task = task
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
        self.ally_hole = np.zeros((self.height, self.width), dtype=np.bool)
        self.ally_traps = np.zeros((self.height, self.width), dtype=np.bool)
        self.entities = dict()
        self.entity_cnt = 0
        self.radar_cd = 0
        self.trap_cd = 0
        self.allies = set()
        self.enemies = set()
        self.radars = set()
        self.traps = set()

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
            if unit_type == 3:
                self.traps.add(u_id)
                self.ally_traps[y, x] = True

    def ore_count(self):
        return self.ore[self.ore > 0].sum()

    def available_ore_count(self):
        # when ally_hole or ally_trap is true oe don't count in the sum
        # the * -1 act as a not()
        return np.multiply(np.multiply(self.ore, self.ally_hole * -1), self.ally_traps * -1).sum()

    def surface_coverd_by_radar(self):
        return len(self.ore[self.ore >= 0])


class Supervizor:
    def __init__(self):
        self.feasible_tasks = set()
        self.desired_radar_poses = {
            (24, 12), (24, 4), (22, 8),
            (18, 4), (18, 12), (14, 8),
            (9, 4), (9, 12), (5, 8)}
        self.assigned_tasks = dict()

    def create_task(self, env):
        self.feasible_tasks = set()
        # Handle Radar
        actual_radar_pose = {
            env.entities[id_radar].get_loc()
            for id_radar in env.radars
        }
        remaining_radar_poses = list(self.desired_radar_poses - actual_radar_pose)
        remaining_radar_poses.sort(reverse=True)
        try:
            if (env.radar_cd == 0) \
                and (len(remaining_radar_poses) > 0) \
                and (env.available_ore_count() < 6):
                pose = remaining_radar_poses.pop()
                self.feasible_tasks.add((Robot.Task.RADAR, pose))
        except IndexError:
            pass

        # Handle ore
        for i, column in enumerate(env.ore.T):
            for j, ore in enumerate(column):
                if ore > 0 and \
                        ((not env.hole[j, i]) or env.ally_hole[j, i]) and \
                        (not env.ally_traps[j, i]):
                    self.feasible_tasks.add(
                        (Robot.Task.ORE, (i, j))
                    )
        print("*****feasible************", file=sys.stderr)
        print("\n".join(["%s:%i,%i" % (x[0].name, x[1][0], x[1][1]) for x in self.feasible_tasks]), file=sys.stderr)

    def assign_tasks(self, env):
        token_tasks = set([env.entities[x].get_task() for x in env.allies])
        print("*****token************", file=sys.stderr)
        print("\n".join(["%s:%i,%i" % (x[0].name, x[1][0], x[1][1]) for x in token_tasks]), file=sys.stderr)
        dispatachable_tasks = self.feasible_tasks - token_tasks
        print("*****dispatch************", file=sys.stderr)
        print("\n".join(["%s:%i,%i" % (x[0].name, x[1][0], x[1][1]) for x in dispatachable_tasks]), file=sys.stderr)
        for ally in env.allies:
            unit = env.entities[ally]
            dispatachable_tasks = sorted(list(dispatachable_tasks),
                                         key=lambda t: unit.dist_with(*t[1]) if (t[0] == Robot.Task.ORE)
                                         else unit.x + abs(unit.y - t[1][1]), reverse=True)
            if (unit.task != Robot.Task.DEAD) and \
                    (not (unit.get_task() in self.feasible_tasks)) and \
                    (unit.get_task()[0] != Robot.Task.RADAR):
                try:
                    t = dispatachable_tasks.pop()
                    print("%s\ntask change: %s:%s => %s:%s" % (
                    unit, unit.get_task()[0].name, unit.get_task()[1], t[0].name, t[1]), file=sys.stderr)
                    # Decompose tuple in multiple args
                except IndexError:
                    t = (Robot.Task.AVAILABLE, (0, 0))
                except KeyError:
                    t = (Robot.Task.AVAILABLE, (0, 0))
                unit.set_task(*t)
            unit.play(env)


def main():
    env = Environment()
    supervizor = Supervizor()

    while True:
        env.parse()

        supervizor.create_task(env)
        supervizor.assign_tasks(env)


if __name__ == '__main__':
    sys.exit(main())
