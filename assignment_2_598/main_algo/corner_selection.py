"""STUDENTS: ADD YOUR CORNER-SELECTION HEURISTIC HERE.

Only edit choose_corner() and add helpers that use its inputs. The simulator
keeps eligibility, observation updates, and deployment rules outside this file.
Never load a map, shelf, future observation, or simulator Sensor from a policy.
"""
from dataclasses import dataclass
import random
from typing import FrozenSet, Mapping, Tuple

Point = Tuple[int, int]


@dataclass(frozen=True)
class Observation:
    """Information available now. Every coordinate is an image cell (x, y).

    Cells absent from both observed sets are UNKNOWN, not known walls.
    distances contains depot-to-cell distances through observed free space only.
    agent_positions includes the fixed depot at index zero.
    """
    width: int
    height: int
    step: int
    deployment_point: Point
    agent_positions: Tuple[Point, ...]
    observed_free: FrozenSet[Point]
    observed_walls: FrozenSet[Point]
    distances: Mapping[Point, int]


def random_corner(candidates: Tuple[Point, ...], observation: Observation,
                  rng: random.Random) -> Point:
    """Original random baseline. Keep this unchanged for comparisons."""
    return rng.choice(candidates)


def choose_corner(candidates: Tuple[Point, ...], observation: Observation,
                  rng: random.Random) -> Point:
    """STUDENT CODE STARTS HERE: replace this random rule with your heuristic.

    candidates is a sorted, nonempty tuple of currently seen, valid, unoccupied
    targets reachable from the depot through observed free cells. Return ONE
    candidate as an (x, y) tuple. State your score and tie-breaking in the report.

    Use observation for known geometry and rng for seeded random tie-breaking.
    Do not change candidates or the simulator's corner-validity convention.
    This starter intentionally supplies no improved heuristic.
    """
    return rng.choice(candidates)
    # STUDENT CODE ENDS HERE.
