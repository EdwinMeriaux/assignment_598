# assignment_2_598

This is a CADENCE corner-selection assignment based on the supplied POCGAGP project. It keeps
only **divided world 1, first 30 PNGs in numeric dungeon order**, portable
visibility-shelf generation, and a CADENCE loop that teleports a **new** agent to
one currently visible valid corner per step. All previously deployed agents stay
in place. A seeded uniform random selector is provided as the baseline.

**Students add their heuristic in
[`main_algo/corner_selection.py`](main_algo/corner_selection.py), inside
`choose_corner()`.** The student policy initially behaves exactly like random
selection. No improved heuristic or assignment solution is supplied.

## Run on macOS, Windows, or Linux

Install Python **3.10 or newer**. The only Python dependency is Pillow. No Rust,
Cargo, C/C++ compiler, PyTorch, SciPy, or plotting/video software is required.

Open a terminal in this folder. On macOS or Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python demo.py
```

On Windows, these commands avoid shell activation requirements:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe demo.py
```

Use the same Python interpreter for the commands below. The demo prepares the
first map if necessary and runs the random baseline with action seed 0 and
deployment seed 0. The first three maps already have portable shelves included.

Look in `outputs/latest/` for:

- `exploration.gif`: current observations, eligible corners, selected corner,
  and stationary agents, updated after each deployment.
- `final.png`: final observed state.
- `result.json`: all candidates and selections, newly observed cells, resource
  counts, termination reason, and summary metrics.

The included example is in [`examples/random_seed_0/`](examples/random_seed_0/).
Gold marks candidates, blue marks agents, pink marks the fixed depot, teal marks
observed free space, and dark cells represent unknown space or observed walls.

## Generate the shelves

```sh
python prepare.py                  # all 30 retained maps
python prepare.py --limit 3        # only the first three
python prepare.py --backend python --limit 1 --force
```

`--backend auto` chooses a bundled executable for the current operating system
and CPU. If unavailable or unable to start, it uses the matching Python
implementation. `--backend native` requires the executable; `--backend python`
forces the slower Python generator. Cached shelves are reused unless the PNG
changes or `--force` is supplied. Generation never invokes Cargo.

Executables are included for Apple Silicon and Intel Macs, x86-64 Windows, and
x86-64 Linux. Both Mac builds were executed during preparation; Windows and
Linux were cross-compiled and inspected, with the Python fallback available on
all three operating systems. See [`bin/README.md`](bin/README.md) for build and
verification details.

Each map has one `dungeon_NUMBER.shelf.dat` data file and one `.shelf.dir` index.
Keep both together. These use Python's portable `dbm.dumb` backend and pickle
protocol 4. Seeds affect deployment/selection, so five identical shelf copies
are unnecessary. Old shelves from the original project need to be regenerated;
this starter expects its metadata and mutual-visibility convention.

## Implement the student policy

`choose_corner(candidates, observation, rng)` must return one `(x, y)` tuple from
`candidates`. The tuple is sorted before selection, so seeded runs do not depend
on shelf order or Python set iteration. `rng` is an isolated `random.Random`
instance seeded by `--seed`.

`observation` contains only current information:

| Field | Meaning |
| --- | --- |
| `observed_free` | Cells currently visible to the deployed network |
| `observed_walls` | Blocked cells on the observed free-space boundary |
| `agent_positions` | Stationary agents, with the fixed depot at index 0 |
| `deployment_point` | Fixed depot coordinates |
| `distances` | Four-neighbor shortest distances from the depot through observed free space |
| `width`, `height`, `step` | Grid size and completed teleport deployments |

All coordinates use **image coordinates: x right, y down**. Cells absent from
both observed sets are unknown. A policy must not open map PNGs, shelves, future
FOV data, or simulator internals. The observation is immutable; its distance
mapping is read-only. This interface limits accidental information leakage; it
is not a security sandbox against deliberately loading hidden data.

Keep `random_corner()` unchanged for fair comparisons. After editing
`choose_corner()`, run:

```sh
python main_algo/CADENCE.py --policy student --seed 0 --output outputs/student_0
python main_algo/CADENCE.py --policy random --seed 0 --output outputs/random_0
```

Deployment seed defaults to 0 independently of the selection seed, so both
policies and all five action seeds use the same start in each map. Change it with
`--deployment-seed 7`, or fix a particular free cell with `--deployment X Y`.
Resource controls are `--step-limit N` and `--max-agents N`.

```sh
python run_experiments.py --maps 3 --seeds 0 1 2 3 4 --policies random student
```

This writes one row per run to `outputs/results.csv` (15 runs per policy by
default). Until the student edits their function, the two policies deliberately
produce identical selections for the same seeds. Students should produce and
interpret their own comparison plots/tables.

## What the simulator checks

The valid-corner sensor follows the blackbox **alpha** interface in Algorithm 1
of [Meriaux et al., *On Mobile Ad Hoc Networks for Coverage of Partially
Observable Worlds*](https://arxiv.org/abs/2512.09495). During offline preparation,
the simulator labels reflex corners and excludes one top-left corner per hole.
At runtime it reports only valid targets already visible to a deployed agent;
the complete corner table and map remain inside the sensor. The policy receives
the filtered eligible targets, not hidden obstacle geometry or candidate FOVs.

In this raster representation, a reflex corner is the meeting vertex of a 2x2
block containing three free cells and one blocked cell. Its deployment target is
the free cell diagonally opposite that blocked cell. A hole is a four-connected
blocked component not touching the image border. Its excluded corner minimizes
`(vertex_y, vertex_x)`, because image y points down. This explicitly applies the
paper's top-left convention; the old helper instead sorted x before y.

A target is eligible only if it is visible, unoccupied, and reachable from the
depot through currently observed free cells. A four-neighbor BFS checks
reachability; the resulting distance is available to the policy. The BFS does
not add observations or simulate motion. Invalid policy outputs fail explicitly
instead of silently substituting another corner.

Visibility uses the original Bresenham raster-line approach, checked in **both
directions** to make LOS mutual when line rounding differs by direction. The
Rust and Python generators use the same test. Boundary observations are blocked
cells four-adjacent to currently visible free cells.

After each teleport, the simulator checks that the new agent has mutual LOS to
at least one previous agent. With the initially connected depot this preserves
endpoint network connectivity by induction. Coverage cannot shrink because
previous agents remain fixed; this is also checked after each deployment.

**This is a teleporting selection exercise, not the original movement simulator.**
Connectivity is checked at deployment endpoints; there is no transit path,
collision model, deallocation, or continuous-time motion guarantee. One reported
step means one teleport deployment, not Euclidean travel time or a movement step.
The continuous geometric bounds in the paper are not asserted for pixel-center
targets and raster LOS. No eligible targets with incomplete coverage is reported
as a failure, not silently reported as success.

`success` means every free cell is covered. The evaluator uses ground truth to
measure this; the policy is not given the total free-cell count or unseen map.
Unsuccessful runs have a blank `steps_to_full_coverage` CSV field. Peak and final
agent counts **include the fixed depot**. They are equal in this variant because
agents are only added; `mobile_agents` excludes the depot.

The assignment PDF's physical movement requirements need to be adjusted if this
teleporting starter is used as the student baseline. Its movement guarantees and
travel-time metric cannot be inferred from teleport runs.

## Files retained

- `Detereministic_ALGO/new_true_world_data/divided_world_1/`: 30 original PNGs,
  retaining their original complexity subfolders and filenames.
- `prepare.py`, `common/`: visibility generation, geometry, sensor, rendering.
- `main_algo/CADENCE.py`: the runnable teleport loop.
- `main_algo/corner_selection.py`: the student edit point and random baseline.
- `demo.py`, `run_experiments.py`: single-run and batch entry points.
- `bin/`, `src/`, `Cargo.toml`, `Cargo.lock`: compiled visibility tools and their
  source. Rust source is retained for the instructor; students need not build it.
- `tests/`: simulator checks, runnable with `python -m unittest discover -s tests -v`.

`MAPS.csv` lists the precise retained maps and hashes. The instructor keeps the
full original project in a separate backup, outside the student ZIP.

## Starter verification

Eight simulator checks passed. Across all 30 retained maps and action seeds
0-4, both the random baseline and the unchanged student placeholder achieved
full coverage (300 runs total, deployment seed 0). These are starter checks,
not evidence of a heuristic improvement. The first-three-map baseline CSV is
included at `examples/baseline_check.csv`. The Python fallback was also compared
against Rust for every free-cell FOV on the first 50x50 map.
