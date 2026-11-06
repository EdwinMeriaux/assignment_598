"""Raster geometry and known-space paths. Coordinates are always (x, y)."""
from collections import deque

NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def neighbors(point):
    x, y = point
    return ((x + dx, y + dy) for dx, dy in NEIGHBORS)


def known_distances(free, source):
    """Four-neighbor BFS using only the supplied observed free cells."""
    distances = {source: 0}
    queue = deque([source])
    while queue:
        point = queue.popleft()
        for nxt in neighbors(point):
            if nxt in free and nxt not in distances:
                distances[nxt] = distances[point] + 1
                queue.append(nxt)
    return distances


def valid_corners(free, width, height):
    """Offline sensor metadata, never passed to a selection policy.

    A 2x2 block with three free cells has a reflex vertex at its center.
    The agent target is the free cell diagonally opposite the blocked cell.
    Exclude the top-left reflex vertex of each enclosed blocked component.
    Image y increases downwards, so top-left minimizes (vertex_y, vertex_x).
    """
    blocked = {(x, y) for y in range(height) for x in range(width)} - free
    remaining = set(blocked)
    labels, holes, component = {}, set(), 0
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue, touches_border = deque([start]), False
        while queue:
            point = queue.popleft()
            labels[point] = component
            x, y = point
            touches_border |= x in (0, width - 1) or y in (0, height - 1)
            for nxt in neighbors(point):
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
        if not touches_border:
            holes.add(component)
        component += 1

    records = []
    for y in range(height - 1):
        for x in range(width - 1):
            cells = ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1))
            walls = [p for p in cells if p in blocked]
            if len(walls) == 1:
                wall = walls[0]
                target = (2*x + 1 - wall[0], 2*y + 1 - wall[1])
                records.append({"vertex": (x + 0.5, y + 0.5), "target": target,
                                "free_neighbors": tuple(p for p in cells if p != wall),
                                "wall": wall, "component": labels[wall]})
    excluded = set()
    for hole in holes:
        candidates = [r for r in records if r["component"] == hole]
        if candidates:
            record = min(candidates, key=lambda r: (r["vertex"][1], r["vertex"][0]))
            excluded.add(record["vertex"])
    return [r for r in records if r["vertex"] not in excluded]


def line_clear(a, b, free):
    """Original Bresenham raster test, without allocating a list of points."""
    x, y = a
    dx, dy = abs(b[0] - x), abs(b[1] - y)
    sx, sy = (1 if x < b[0] else -1), (1 if y < b[1] else -1)
    err = dx - dy
    while True:
        if (x, y) not in free:
            return False
        if (x, y) == b:
            return True
        twice = 2 * err
        if twice > -dy:
            err -= dy
            x += sx
        if twice < dx:
            err += dx
            y += sy
