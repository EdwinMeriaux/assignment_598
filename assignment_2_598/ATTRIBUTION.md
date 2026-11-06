# Sources and changes

The 30 world PNGs were copied without alteration from the supplied
`Detereministic_ALGO/new_true_world_data/divided_world_1`.
Their original paths and SHA-256 hashes appear in `MAPS.csv`.

The teleport deployment loop and raster geometry are a simplified teaching
adaptation of the supplied `main_algo/CADENCE.py`, `CADENCE_teleport.py`,
`common/angles.py`, `common/other_functions.py`, and `src/main.rs`.

The associated method is described in E. Meriaux et al.,
[*On Mobile Ad Hoc Networks for Coverage of Partially Observable Worlds*](https://arxiv.org/abs/2512.09495),
especially Sections II-IV and Algorithm 1.

The starter removes unrelated algorithms, learned models, datasets, experimental
results, intermediate images, machine-specific launchers, and build caches. It
replaces travel and deallocation with sequential addition of stationary agents,
isolates policy inputs, seeds selection separately from deployment, makes LOS
mutual by testing both Bresenham directions, applies the paper's top-left hole
exclusion in image coordinates, and stores one portable shelf per map.

The full original source is preserved in the sibling backup folder. This
adaptation does not assign a new license to the supplied project or maps.
Notices for libraries in the bundled native executables are included in
`THIRD_PARTY_NOTICES.txt`. Pillow is installed separately by pip under its own
license.
