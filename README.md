# assignment_2_598

Design a corner-selection heuristic for CADENCE. The starter chooses a currently
visible valid corner uniformly at random and teleports one new agent there.
Earlier agents stay in place as the world is revealed.

## Setup and run

Use **Python 3.10 or newer**. Pillow is the only dependency. Rust and build tools
are not needed.

Open a terminal in the `assignment_2_598` folder. On macOS or Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main_algo/CADENCE.py
```

On Windows:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main_algo/CADENCE.py
```

The run automatically generates visibility data for its map if needed. Results
go to `assignment_2_598/outputs/latest/`: `exploration.gif`, `final.png`, and
`result.json`, which records eligible corners, selections, coverage, and counts.

## Add your code here

Edit **[`choose_corner()` in corner_selection.py](assignment_2_598/main_algo/corner_selection.py)**.
Return one `(x, y)` tuple from `candidates`. The starter's student function is
random until you replace it with your heuristic. Keep `random_corner()` as the
baseline.

Your function receives the eligible targets, a seeded random generator, and the
current observation: visible free cells, observed boundary walls, agent
positions, the depot, and distances through observed free space. Coordinates use
image axes: x points right and y points down. Other cells are unknown. Use only
these inputs; do not read map images, shelves, hidden corner tables, or future
visibility data. Specify how your heuristic breaks ties.

From the `assignment_2_598` folder, compare the two policies:

```sh
python main_algo/CADENCE.py --policy random --seed 0 --output outputs/random
python main_algo/CADENCE.py --policy student --seed 0 --output outputs/student
```

Both use deployment seed 0 by default, independently of the selection seed.
Options include `--deployment-seed`, `--deployment X Y`, `--step-limit`, and
`--max-agents`. Agent counts include the fixed depot.

## Maps and shelf generation

The first 30 maps in numeric dungeon order from divided world 1 are in
`assignment_2_598/worlds/divided_world_1/`. To select another map or prepare all
maps in advance, run from `assignment_2_598`:

```sh
python main_algo/CADENCE.py --map worlds/divided_world_1/dungeon_83.png
python prepare.py
```

Shelf generation uses a bundled executable for Apple Silicon or Intel macOS,
x86-64 Windows, or x86-64 Linux. Other systems automatically use the Python
fallback. To force the fallback for the first map:

```sh
python prepare.py --limit 1 --backend python --force
```

One portable shelf is generated per map and reused across seeds. The `.shelf.dat`
and `.shelf.dir` files belong together. Generated shelves and run outputs are
ignored by Git. Both Mac binaries were executed during preparation; the Windows
and Linux binaries were cross-compiled and inspected.

## Simulation model

A valid raster corner comes from a 2x2 block with three free cells and one wall
cell; its target is the free cell diagonally opposite the wall. One top-left
corner per hole is excluded. The simulator precomputes these labels as the
paper's corner sensor, then supplies only visible, unoccupied targets reachable
through observed free space. Hidden map data is not passed to the policy.

Visibility uses Bresenham line checks in both directions. Each new agent must
have mutual line of sight to the existing network. Existing agents stay fixed,
preserving their coverage. These checks concern teleport endpoints: motion and
continuous-time connectivity are not simulated. A time step counts one teleport
deployment. Full coverage means every free cell is visible; an incomplete run
reports its termination reason.

## Reference

The maps and CADENCE adaptation come from the supplied POCGAGP project. See
Meriaux et al., [*On Mobile Ad Hoc Networks for Coverage of Partially Observable
Worlds*](https://arxiv.org/abs/2512.09495), Sections II-IV. Library notices for the
compiled tools are in `assignment_2_598/bin/THIRD_PARTY_NOTICES.txt`.
