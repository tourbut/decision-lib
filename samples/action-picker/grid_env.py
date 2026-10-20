"""A text grid world with two layers, as in minecraft-agent: a rule-based planner sets the
current subgoal, and the decision model picks one valid action toward it each turn.

The observation is compressed to what matters (position, what is in each direction,
inventory) and only actions that are legal right now are offered, so the controller
cannot walk into a wall. When the stage changes (the key is picked up, the door opens),
the stage guard throws the old subgoal away and asks the planner again.

Legend: # wall, . floor, S start, K key, D locked door, E exit, T torch and C chest
(decoys the plan does not need).
"""

from __future__ import annotations

from collections import deque
from typing import NamedTuple

MAPS = {
    "corridor": ["#######",
                 "#S.TK.#",
                 "#####D#",
                 "#E....#",
                 "#######"],
    "rooms": ["#########",
              "#S..#..K#",
              "#.#.#.#.#",
              "#C#...#.#",
              "#D#######",
              "#E......#",
              "#########"],
    "detour": ["########",
               "#S.#.TE#",
               "#..#.###",
               "#.CD...#",
               "#K######",
               "########"],
}

MOVES = {"north": (-1, 0), "south": (1, 0), "west": (0, -1), "east": (0, 1)}
NAMES = {"north": "북쪽", "south": "남쪽", "west": "서쪽", "east": "동쪽"}


class State(NamedTuple):
    map: str
    pos: tuple[int, int]
    has_key: bool
    door_open: bool
    taken: tuple[str, ...] = ()  # decoys picked up


def cell(state: State, pos: tuple[int, int]) -> str:
    return MAPS[state.map][pos[0]][pos[1]]


def find(name: str, char: str) -> tuple[int, int]:
    return next((r, c) for r, row in enumerate(MAPS[name]) for c, ch in enumerate(row) if ch == char)


def start(name: str) -> State:
    return State(name, find(name, "S"), False, False)


def passable(state: State, pos: tuple[int, int]) -> bool:
    ch = cell(state, pos)
    return ch != "#" and (ch != "D" or state.door_open)


def stage(state: State) -> str:
    """The planner's stage; a change of stage invalidates the current subgoal."""
    if not state.has_key:
        return "get_key"
    if not state.door_open:
        return "open_door"
    return "exit"


def planner(state: State) -> str:
    """System 2 stand-in: a fixed rule per stage, written as an instruction."""
    return {"get_key": "열쇠(K)를 주워라.", "open_door": "잠긴 문(D) 앞으로 가서 문을 열어라.",
            "exit": "출구(E)로 가라."}[stage(state)]


def distance(state: State, target: tuple[int, int], frm: tuple[int, int] | None = None) -> int | None:
    """Shortest walk; a locked door counts as reachable as a destination."""
    frm = frm or state.pos
    seen, queue = {frm}, deque([(frm, 0)])
    while queue:
        pos, d = queue.popleft()
        if pos == target:
            return d
        for dr, dc in MOVES.values():
            nxt = (pos[0] + dr, pos[1] + dc)
            if nxt not in seen and (passable(state, nxt) or nxt == target):
                seen.add(nxt)
                queue.append((nxt, d + 1))
    return None


TARGET = {"get_key": "K", "open_door": "D", "exit": "E"}
PLAN_EVERY = 5  # the slow planner refreshes on this cadence, or at once when the stage changes


class GridEnv:
    """Keeps the planner's subgoal between turns. The stage guard drops it the moment the
    stage changes, instead of waiting for the next scheduled refresh.

    hints="offset" shows only where the target is (north 2, west 4). hints="distance" also
    labels each move with the walking distance to the target. hints="macro" offers
    high-level actions instead (go to the key, open the door, go to the exit, and the
    decoys), and code walks the shortest path: the split minecraft-agent uses, where Jev
    picks the action and Mineflayer's pathfinder moves."""

    def __init__(self, hints: str = "distance") -> None:
        self.hints = hints
        self.plan: str | None = None
        self.plan_stage: str | None = None
        self.since_plan = 0
        self.replans: list[str] = []
        self.moves = 0  # single-cell moves actually walked, macro or not

    def _plan(self, state: State) -> str:
        if self.plan is not None and self.plan_stage != stage(state):
            self.replans.append(f"단계 변경({self.plan_stage} → {stage(state)}): 낡은 계획 폐기")
            self.plan = None
        elif self.plan is not None and self.since_plan >= PLAN_EVERY:
            self.replans.append("정기 갱신")
            self.plan = None
        if self.plan is None:
            self.plan, self.plan_stage, self.since_plan = planner(state), stage(state), 0
        self.since_plan += 1
        return self.plan

    def observe(self, state: State) -> tuple[str, dict[str, str]]:
        if self.hints == "macro":
            return self._observe_macro(state)
        plan = self._plan(state)
        tr, tc = find(state.map, TARGET[stage(state)])
        dr, dc = tr - state.pos[0], tc - state.pos[1]
        offset = " ".join(filter(None, [f"{'남' if dr > 0 else '북'}쪽 {abs(dr)}칸" if dr else "",
                                        f"{'동' if dc > 0 else '서'}쪽 {abs(dc)}칸" if dc else ""])) or "바로 여기"
        candidates, around = {}, []
        for move, (mr, mc) in MOVES.items():
            nxt = (state.pos[0] + mr, state.pos[1] + mc)
            ch = cell(state, nxt)
            around.append(f"{NAMES[move]} {'벽' if ch == '#' else '잠긴 문' if ch == 'D' and not state.door_open else '통로'}")
            if ch == "D" and state.has_key and not state.door_open:
                candidates["open_door"] = f"{NAMES[move]}의 문을 연다"
            if passable(state, nxt):
                d = distance(state, (tr, tc), nxt) if self.hints == "distance" else None
                candidates[move] = f"{NAMES[move]}으로 한 칸 이동" + ("" if d is None else f" (그 뒤 목표까지 {d}걸음)")
        if cell(state, state.pos) == "K" and not state.has_key:
            candidates["pick_key"] = "발밑의 열쇠를 줍는다"
        where = f"목표 위치(직선): {offset}\n"
        if self.hints == "distance":
            where += "벽 때문에 직선으로 못 갈 수 있다. 각 이동의 걸음 수가 벽을 돌아가는 실제 거리다.\n"
        text = (f"계획: {plan}\n{where}주변: {', '.join(around)}\n"
                f"인벤토리: {'열쇠' if state.has_key else '없음'}\n발밑: {'출구' if cell(state, state.pos) == 'E' else '바닥'}")
        return text, candidates

    def _observe_macro(self, state: State) -> tuple[str, dict[str, str]]:
        plan = self._plan(state)
        here = cell(state, state.pos)
        candidates = {}
        for ch, name in (("K", "열쇠"), ("T", "횃불"), ("C", "상자"), ("E", "출구")):
            if ch not in "".join(MAPS[state.map]) or (ch == "K" and state.has_key) or ch in state.taken:
                continue
            pos = find(state.map, ch)
            d = distance(state, pos)
            if pos != state.pos and d is not None and passable(state, pos):
                candidates[f"goto_{ch}"] = f"{name}(으)로 이동 ({d}걸음)"
        if here == "K" and not state.has_key:
            candidates["pick_key"] = "발밑의 열쇠를 줍는다"
        if here in "TC" and here not in state.taken:
            candidates[f"take_{here}"] = f"발밑의 {'횃불' if here == 'T' else '상자'}을(를) 챙긴다"
        door = find(state.map, "D")
        if not state.door_open and state.has_key:
            if distance(state, door) == 1:
                candidates["open_door"] = "옆의 잠긴 문을 연다"
            elif distance(state, door) is not None:
                candidates["goto_D"] = f"잠긴 문 앞으로 이동 ({distance(state, door) - 1}걸음)"
        text = (f"계획: {plan}\n인벤토리: {', '.join(['열쇠'] * state.has_key + list(state.taken)) or '없음'}\n"
                f"문: {'열림' if state.door_open else '잠김'}\n발밑: {'출구' if here == 'E' else '바닥'}")
        return text, candidates

    def step(self, state: State, action: str) -> State:
        if action == "pick_key":
            return state._replace(has_key=True)
        if action == "open_door":
            return state._replace(door_open=True)
        if action.startswith("take_"):
            return state._replace(taken=(*state.taken, action[-1]))
        if action.startswith("goto_"):
            target = find(state.map, action[-1])
            if action == "goto_D":  # stand beside the door, on the side we can reach
                d = distance(state, target)
                target = next(p for p in ((target[0] + dr, target[1] + dc) for dr, dc in MOVES.values())
                              if passable(state, p) and distance(state, p) == d - 1)
            self.moves += distance(state, target)
            return state._replace(pos=target)
        self.moves += 1
        dr, dc = MOVES[action]
        return state._replace(pos=(state.pos[0] + dr, state.pos[1] + dc))


def at_exit(state: State) -> bool:
    return cell(state, state.pos) == "E"


def optimal_steps(name: str) -> int:
    """Moves plus the two pick/open actions on the shortest route, for comparison."""
    s = start(name)
    key, door, exit_ = find(name, "K"), find(name, "D"), find(name, "E")
    to_key = distance(s, key)
    with_key = s._replace(pos=key, has_key=True)
    to_door = distance(with_key, door) - 1  # stand next to the door
    opened = with_key._replace(door_open=True)
    beside = next(p for p in ((door[0] + dr, door[1] + dc) for dr, dc in MOVES.values())
                  if passable(opened, p) and distance(with_key, p) == to_door)
    return to_key + 1 + to_door + 1 + distance(opened._replace(pos=beside), exit_)
