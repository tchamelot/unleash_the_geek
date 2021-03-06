import sys
from enum import IntEnum
from collections import deque
import numpy as np


class Entity:
    """
    Base class for entity on the map
    """

    def __init__(self, x, y, item=-1):
        """
        Create a new entity at ```x```, ```y``` with ```item```
        """
        self.x = x
        self.old_x = x
        self.y = y
        self.old_y = y
        self.item = item
        self.old_item = item

    def __str__(self):
        """
        Print position of the Entity
        """
        return '%i %i' % (self.x, self.y)

    def __repr__(self):
        """
        Print position of the Entity
        """
        return '%i %i' % (self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def update(self, x, y, item):
        """
        Update an entity without calling the constructor again
        """
        self.old_x = self.x
        self.old_y = self.y
        self.old_item = item
        self.x = x
        self.y = y
        self.item = item

    def get_loc(self):
        return self.x, self.y

    def dist_with(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)


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
        self.task = Robot.Task.AVAILABLE
        self.assigned_task = Robot.Task.AVAILABLE
        self.target = Entity(
            x=5 + np.random.randint(-2, 2),
            y=7 + np.random.randint(-2, 2),
        )
        self.action = 'DIG %i %i AVAIL_DIG' % (self.target.x, self.target.y)
        self.tid = 0

    def update(self, x, y, item):
        super().update(x, y, item)
        if (x < 0) or (y < 0):
            self.task = Robot.Task.DEAD
            self.assigned_task = Robot.Task.DEAD

    def radar(self, env):
        if self.task == Robot.Task.RADAR:
            self.action = 'REQUEST RADAR REQ RADAR'
            if self.item == 2:
                self.task = Robot.Task.PLACE_RADAR
        if self.task == Robot.Task.PLACE_RADAR:
            self.action = 'DIG %s DIG RADAR' % self.target
            if self.item != 2:
                self.on_available(env)

    def ore(self, env):
        if self.task == Robot.Task.ORE:
            self.action = 'DIG %s DIG ORE' % self.target
            if (self.x == 0) and \
                    (env.trap_cd == 0) and \
                    (self.item == -1) and \
                    (env.ore[self.target.y, self.target.x] == 1):
                self.action = "REQUEST TRAP REQ TRAP"
                env.trap_cd = 5
            elif (self.x == 0) and \
                    (env.radar_cd == 0) and \
                    (self.item == -1):
                self.action = "REQUEST RADAR REQ RAD"
                env.radar_cd = 5
            else:
                if self.item == 4:
                    self.task = Robot.Task.BASE
                    env.ally_hole[self.target.y, self.target.x] = True
                elif not (env.is_trap_free(self.target.x, self.target.y) or env.unsafe_ore_condition):
                    self.on_available(env)
                # if (self.item == 3) and (self.dist_with(*self.target)<3):
                #     env.ally_traps[self.target[1], self.target[0]] = True
                #     # self.task = Robot.Task.BASE
        if self.task == Robot.Task.BASE:
            self.action = 'MOVE 0 %s MOVE ORE' % self.y
            if self.item == -1:
                self.on_available(env)

    def on_available(self, env):
        self.task = Robot.Task.AVAILABLE
        self.assigned_task = Robot.Task.AVAILABLE
        if env.next_radar_pose is not None:
            self.target = Entity(
                x=min(env.width - 1, env.next_radar_pose.x + np.random.randint(-3, 3)),
                y=min(env.height - 1, env.next_radar_pose.y + np.random.randint(-3, 3)),
            )
            if env.trap_free[self.target.y, self.target.x]:
                self.action = 'DIG %i %i AVAIL_DIG' % (self.target.x, self.target.y)
        else:
            self.action = "WAIT NO_ACTION"

    def play(self, env):
        """
        Output the robot action for the current round
        """
        if self.item == 4:
            self.task = Robot.Task.ORE
        if self.task == Robot.Task.AVAILABLE:
            self.action = 'DIG %i %i WAIT' % (self.target.x, self.target.y)
            if env.hole[self.target.y, self.target.x] != 0:
                self.on_available(env)
            elif self.item == 4:
                env.ally_hole[self.target.y, self.target.x] = True
        elif self.task <= Robot.Task.RADAR:
            self.radar(env)
        elif self.task <= Robot.Task.ORE:
            self.ore(env)
        elif self.task == Robot.Task.DEAD:
            self.action = 'WAIT DEAD'

        self.action += " %s" % self.target

        print(self.action)

    def __str__(self):
        return "robot:\nloc:%i,%i\nstatus:%s task:%s" % (self.x, self.y, self.task.name, self.assigned_task.name)

    def get_task(self):
        return self.assigned_task, self.target, self.tid

    def set_task(self, task, target, tid):
        self.task = task
        self.assigned_task = task
        self.target = target
        self.tid = tid


ENTITY_FACTORY = {
    0: Robot,
    1: Entity,
    2: Entity,
    3: Entity,
}


class Environment:

    def __init__(self):
        # Get map dimensions
        self.width, self.height = [int(i) for i in input().split()]
        self.my_score = 0
        self.enemy_score = 0
        self.next_radar_pose = Entity(5, 7)
        self.unsafe_ore_condition = False
        self.turn = 0
        self.ore = np.zeros((self.height, self.width), dtype=np.int8)
        self.hole = np.zeros((self.height, self.width), dtype=np.bool)
        self.ally_hole = np.zeros((self.height, self.width), dtype=np.bool)
        self.ally_traps = np.zeros((self.height, self.width), dtype=np.bool)
        self.trap_free = np.zeros((self.height, self.width), dtype=np.bool)
        self.entities = dict()
        self.radar_cd = 0
        self.trap_cd = 0
        self.allies = set()
        self.enemies = set()
        self.radars = set()

    def parse(self):
        # Get the score
        self.radars = set()
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
        self.ore[self.ore <= 0] = 0
        entity_cnt, self.radar_cd, self.trap_cd = np.vectorize(np.uint8)(
            input().split()
        )
        for i in range(entity_cnt):
            u_id, unit_type, x, y, item = [int(j) for j in input().split()]
            try:
                self.entities[u_id].update(x, y, item)
            except KeyError:
                self.entities[u_id] = ENTITY_FACTORY[unit_type](x, y, item)
                if unit_type == 0:
                    self.allies.add(u_id)
                elif unit_type == 1:
                    self.enemies.add(u_id)
                elif unit_type == 3:
                    self.ally_traps[y, x] = True
            if unit_type == 2:
                self.radars.add(u_id)
        self.trap_free = np.logical_and(
                np.logical_or(np.logical_not(self.hole), self.ally_hole),
                np.logical_not(self.ally_traps)
            )
        self.turn += 1

    def ore_count(self):
        return self.ore[self.ore > 0].sum()

    def available_ore_count(self):
        # when ally_hole or ally_trap is true oe don't count in the sum
        # the * -1 act as a not()
        return np.multiply(self.ore, self.trap_free).sum()

    def surface_coverd_by_radar(self):
        return len(self.ore[self.ore >= 0])

    def unsafe_ore_count(self):
        return np.multiply(np.logical_and(np.logical_not(self.ally_traps), self.ally_hole), self.ore).sum()

    def is_trap_free(self, x, y):
        return self.trap_free[y, x]


class Supervizor:
    def __init__(self):
        self.feasible_tasks = set()
        self.desired_radar_poses = {Entity(28, 7),
                                    Entity(24, 11), Entity(24, 3), Entity(23, 7),
                                    Entity(18, 3), Entity(18, 11), Entity(15, 7),
                                    Entity(10, 3), Entity(10, 11), Entity(6, 7)}
        self.assigned_tasks = dict()

    def create_task(self, env):
        self.feasible_tasks = set()
        # Handle Radar
        radar_pose = {env.entities[id_radar] for id_radar in env.radars}
        remaining_radar = list(filter(lambda rad: env.trap_free[rad.y, rad.x], self.desired_radar_poses - radar_pose))
        remaining_radar.sort(key=lambda r: r.x, reverse=True)
        if len(remaining_radar) == 0:
            env.next_radar_pose = None
        # try:
        if (env.radar_cd == 0) and (env.available_ore_count() < 10) and (len(remaining_radar) > 0):
            pose = remaining_radar.pop()
            env.next_radar_pose = pose
            self.feasible_tasks.add((Robot.Task.RADAR, pose, 0))
        # except IndexError:
        #     pass

        # Handle ore
        # env.turn > 175 and (env.my_score < env.enemy_score) and
        env.unsafe_ore_condition = (env.turn > 130) and (env.available_ore_count() <= 10)
        for x, column in enumerate(env.ore.T):
            for y, ore in enumerate(column):
                if ore > 0 and ((env.is_trap_free(x, y) or env.unsafe_ore_condition)):
                    for o in range(ore):
                        self.feasible_tasks.add(
                                (Robot.Task.ORE, Entity(x, y), o)
                        )

        print("safe_ore_count: %i, next radar pose: %s" % (env.available_ore_count(), env.next_radar_pose), file=sys.stderr)
        print("unsafe mode %s" % env.unsafe_ore_condition, file=sys.stderr)
        print("*****feasible************", file=sys.stderr)
        print("\n".join(["%s:%i,%i" % (x[0].name, x[1].x, x[1].y) for x in self.feasible_tasks]), file=sys.stderr)

    def assign_tasks(self, env):
        taken_tasks = set([env.entities[x].get_task() for x in env.allies])

        print("*****taken************", file=sys.stderr)
        print("\n".join(["%s:%i,%i" % (x[0].name, x[1].x, x[1].y) for x in taken_tasks]), file=sys.stderr)

        dispatchable_tasks = self.feasible_tasks - taken_tasks

        print("*****dispatch************", file=sys.stderr)
        print("\n".join(["%s:%i,%i" % (x[0].name, x[1].x, x[1].y) for x in dispatchable_tasks]), file=sys.stderr)

        for ally in env.allies:
            unit = env.entities[ally]

            dispatchable_tasks = sorted(
                list(dispatchable_tasks),
                key=lambda t: unit.dist_with(t[1]) if (t[0] == Robot.Task.ORE)
                else unit.x + abs(unit.y - t[1].y), reverse=True
            )

            if (unit.task != Robot.Task.DEAD) and \
                    (not (unit.get_task() in self.feasible_tasks)) and \
                    (unit.item != 2) and \
                    (unit.item != 4):
                try:
                    t = dispatchable_tasks.pop()
                    print("%s\ntask change: %s:%s => %s:%s" % (
                        unit, unit.get_task()[0].name, unit.get_task()[1],
                        t[0].name, t[1]
                    ),
                          file=sys.stderr)
                    # Decompose tuple in multiple args
                    unit.set_task(*t)
                except LookupError:
                    pass
                    # unit.on_available(env)
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
