import sys
from enum import IntEnum
import numpy as np


class Entity:
    """
    Base class for entity on the map
    """

    def __init__(self, x, y, item=-1, uid=-1):
        """
        Create a new entity at ```x```, ```y``` with ```item```
        """
        self.x = x
        self.old_x = x
        self.y = y
        self.old_y = y
        self.item = item
        self.old_item = item
        self.uid = uid
        self.base = False

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
        return int(abs(self.x - other.x)/4 + abs(self.y - other.y)/4)


def dist(t1, t2):
    return abs(t1[0] - t2[0]) + abs(t1[1] - t2[0])


class Item(IntEnum):
    NONE = -1
    RADAR = 2
    TRAP = 3
    ORE = 4


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

    def __init__(self, x, y, item, uid):
        super().__init__(x, y, item, uid)
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
            # if (self.x <= 4) and \
            #         (env.trap_cd == 0) and \
            #         (self.item == -1) and \
            #         (env.ore[self.target.y, self.target.x] == 2) and \
            #         (env.my_score > env.enemy_score):
            #     self.action = "REQUEST TRAP REQ TRAP"
            #     env.trap_cd = 5
            # # elif (self.x <= 4) and \
            # #         (env.radar_cd == 0) and \
            # #         (self.item == -1):
            # #     self.action = "REQUEST RADAR REQ RAD"
            # #     env.radar_cd = 5
            # else:
            if self.item == 4:
                self.task = Robot.Task.BASE
            elif not (env.is_trap_free(self.target.x, self.target.y) or env.unsafe_ore_condition):
                self.on_available(env)
            if (self.item == 3) and (self.dist_with(self.target)<3):
                env.ally_traps[self.target.y, self.target.x] = True
                # self.task = Robot.Task.BASE
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
            i = 0
            while not(env.trap_free[self.target.y, self.target.x]) \
                    and (not env.known_tiles[self.target.y, self.target.x]) \
                    and (i < 10):
                self.target = Entity(
                    x=min(env.width - 1, env.next_radar_pose.x + np.random.randint(-3, 3)),
                    y=min(env.height - 1, env.next_radar_pose.y + np.random.randint(-3, 3)),
                )
                i += 1
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
        self.diggable_ore = np.zeros((self.height, self.width), dtype=np.int8)
        self.hole = np.zeros((self.height, self.width), dtype=np.bool)
        self.ally_traps = np.zeros((self.height, self.width), dtype=np.bool)
        self.enemy_holes = np.zeros((self.height, self.width), dtype=np.bool)
        self.known_tiles = np.zeros((self.height, self.width), dtype=np.bool)
        self.trap_free = np.zeros((self.height, self.width), dtype=np.bool)
        self.dig_patch = np.array([[False, True, False],
                                   [True, True, True],
                                   [False, True, False]], dtype=np.bool)
        self.radar_patch = np.array([[False, False, False, False,  True, False, False, False, False],
       [False, False, False,  True,  True,  True, False, False, False],
       [False, False,  True,  True,  True,  True,  True, False, False],
       [False,  True,  True,  True,  True,  True,  True,  True, False],
       [ True,  True,  True,  True,  True,  True,  True,  True,  True],
       [False,  True,  True,  True,  True,  True,  True,  True, False],
       [False, False,  True,  True,  True,  True,  True, False, False],
       [False, False, False,  True,  True,  True, False, False, False],
       [False, False, False, False,  True, False, False, False, False]], dtype=bool)
        self.entities = dict()
        self.radar_cd = 0
        self.trap_cd = 0
        self.allies = set()
        self.enemies = set()
        self.radars = set()

    def parse(self):
        # STEP 1: parse all current entities
        # Get the score
        self.current_radars = set()
        self.current_enemies = set()
        self.current_allies = set()
        self.current_ally_traps = np.zeros((self.height, self.width), dtype=np.bool)
        self.current_ore = np.zeros((self.height, self.width), dtype=np.int8)
        self.current_holes = np.zeros((self.height, self.width), dtype=np.bool)
        self.my_score, self.enemy_score = [int(i) for i in input().split()]
        # Get the map
        for i in range(self.height):
            row = np.vectorize(np.uint8)(
                input().replace('?', '-1')  # replace ? in the string
                    .split()  # convert to to array
            )  # convert this to int
            self.current_ore[i, :] = row[0::2]  # 1 over 2 element starting at 0
            self.current_holes[i, :] = row[1::2]  # 1 over 2 elements starting at 1
        # Get entities
        entity_cnt, self.current_radar_cd, self.current_trap_cd = np.vectorize(np.uint8)(
            input().split()
        )
        for i in range(entity_cnt):
            u_id, unit_type, x, y, item = [int(j) for j in input().split()]
            try:
                self.entities[u_id].update(x, y, item)
            except KeyError:
                self.entities[u_id] = ENTITY_FACTORY[unit_type](x, y, item, u_id)
            if unit_type == 0:
                self.current_allies.add(u_id)
            elif unit_type == 1:
                self.current_enemies.add(u_id)
            elif unit_type == 2:
                self.current_radars.add(u_id)
            elif unit_type == 3:
                self.current_ally_traps[y, x] = True
        # STEP 2: update game perception using current entities knowledge
        self.allies = self.current_allies.copy()
        self.radars = self.current_radars.copy()
        for unseen_enemy in self.enemies - self.current_enemies:
            self.entities[unseen_enemy].update(-1, -1, -1)
        for unseen_enemy in self.current_enemies & self.enemies:
            enemy = self.entities[unseen_enemy]
            if (enemy.x < enemy.old_x) and not(enemy.base):
                min_y = max(enemy.old_y-1, 0)
                max_y = min(enemy.old_y+2, self.height)
                min_x = max(enemy.old_x-1, 0)
                max_x = min(enemy.old_x+2, self.width)
                # todo: fix when dig < 1
                self.enemy_holes[min_y:max_y, min_x:max_x] = np.logical_or(
                    self.enemy_holes[min_y:max_y, min_x:max_x],
                    np.logical_and(
                        self.hole[min_y:max_y, min_x:max_x],
                        self.dig_patch[0:max_y - min_y, 0:max_x - min_x]
                    )
                )
                enemy.base = True
            elif enemy.x > enemy.old_x:
                enemy.base = False
        self.trap_cd = self.current_trap_cd
        self.radar_cd = self.current_radar_cd
        self.enemies = self.current_enemies.copy()
        self.known_tiles = self.current_ore != -1
        self.ore = self.current_ore.copy()
        self.ore[self.ore <= 0] = 0
        self.hole = self.current_holes.copy()
        self.ally_traps = self.current_ally_traps.copy()
        self.turn += 1
        # STEP 3 compute estimation of full state
        self.refresh_trap_free()
        # print(np.array(self.trap_free, dtype=np.int8), file=sys.stderr)
        # print(self.hole², file=sys.stderr)
        # print(self.known_tiles, file=sys.stderr)
        # print(self.trap_free, file=sys.stderr)
        # print(self.ally_traps, file=sys.stderr)

    def refresh_trap_free(self):
        self.trap_free = np.logical_and(
                np.logical_not(self.enemy_holes),
                np.logical_not(self.ally_traps)
            )
        self.diggable_ore = np.multiply(self.trap_free, self.ore)

    def get_radar(self):
        self.radar_cd = 5

    def get_trap(self):
        self.trap_cd = 5

    def dig_ore(self, entity):
        self.ore[entity.y, entity.x] -= 1

    def put_trap(self, entity):
        self.ally_traps[entity.y, entity.x] = True
        self.refresh_trap_free()

    def put_radar(self, entity):
        self.radars.add(ENTITY_FACTORY[Item.RADAR](entity.x, entity.y))
        min_y = max(entity.y - 4, 0)
        max_y = min(entity.y + 5, self.height)
        min_x = max(entity.x - 4, 0)
        max_x = min(entity.x + 5, self.width)
        # todo fix when radar loc < 5
        self.known_tiles[min_y:max_y, min_x:max_x] = np.logical_or(
            self.known_tiles[min_y:max_y, min_x:max_x],
            self.radar_patch[0:max_y - min_y, 0:max_x - min_x]
        )

    def deposit_ore(self):
        self.my_score += 1

    def ore_count(self):
        return self.ore[self.ore > 0].sum()

    def available_ore_count(self):
        return np.multiply(self.ore, self.trap_free).sum()

    def get_surface_coverd_by_radar(self):
        return np.sum(self.known_tiles)

    def is_trap_free(self, x, y):
        return self.trap_free[y, x]


class Supervizor:
    def __init__(self):
        self.feasible_tasks = set()
        # self.desired_radar_poses = {Entity(4, 4), Entity(7, 10),
        #                             Entity(12, 5), Entity(16,10), Entity(20, 4),
        #                             Entity(25, 9), Entity(26, 4), Entity(26, 10)}
        self.desired_radar_poses = {Entity(27, 4), Entity(27, 10),
                                    Entity(24-2, 11), Entity(24-2, 3), Entity(23-2, 7),
                                    Entity(18-2, 3), Entity(18-2, 11), Entity(15-2, 7),
                                    Entity(10, 3), Entity(10, 11), Entity(6, 7)}
        self.assigned_tasks = dict()

    def create_task(self, env):
        self.feasible_tasks = set()
        # Handle Radar
        radar_pose = {env.entities[id_radar] for id_radar in env.radars}
        remaining_radar = list(
            # filter(
            #     lambda rad: not env.known_tiles[rad.y, rad.x],
                self.desired_radar_poses - radar_pose
            # )
        )
        remaining_radar.sort(key=lambda r: r.x, reverse=True)
        if len(remaining_radar) == 0:
            env.next_radar_pose = None
        try:
            if (env.radar_cd == 0) and (env.available_ore_count() < 12) and (len(remaining_radar) > 0):
                pose = remaining_radar.pop()
                if not(env.trap_free[pose.y, pose.x]):
                    self.desired_radar_poses.remove(pose)
                    pose.x += 1
                    self.desired_radar_poses.add(pose)
                env.next_radar_pose = pose
                self.feasible_tasks.add((Robot.Task.RADAR, pose, 0))
        except IndexError:
            pass

        # Handle ore
        # env.turn > 175 and (env.my_score < env.enemy_score) and
        env.unsafe_ore_condition = ((env.turn > 190) or (env.next_radar_pose is None))\
                                   and (env.available_ore_count() < 4)
        for x, column in enumerate(env.ore.T):
            for y, ore in enumerate(column):
                if ore > 0 and ((env.is_trap_free(x, y) or env.unsafe_ore_condition)):
                    for o in range(ore):
                        self.feasible_tasks.add(
                                (Robot.Task.ORE, Entity(x, y), o)
                        )

        print("safe_ore_count: %i, surf_cov: %s" % (env.available_ore_count(), env.get_surface_coverd_by_radar()), file=sys.stderr)
        print("enemies loc: %s" % ([env.entities[en]for en in env.enemies]), file=sys.stderr)
        print("unsafe mode %s" % env.unsafe_ore_condition, file=sys.stderr)
        print("*****feasible************", file=sys.stderr)
        print("\n".join(["%s:%i,%i" % (x[0].name, x[1].x, x[1].y) for x in self.feasible_tasks]), file=sys.stderr)

    @staticmethod
    def score_tasks(t, unit):
        if t[0] == Robot.Task.ORE:
            return unit.dist_with(t[1])
        else:
            return unit.x + int(abs(unit.y - t[1].y) / 4) - 4 * (unit.item == Item.ORE)

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
                key=lambda t: Supervizor.score_tasks(t, unit), reverse=not(env.unsafe_ore_condition)
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
