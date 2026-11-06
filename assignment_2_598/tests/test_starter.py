"""Checks for the simulator contract, separate from students' policy design."""
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from common.geometry import known_distances, valid_corners
from common.visibility import (Sensor, map_files, native_binary, open_shelf,
                               prepare_map, python_visibility, read_map)
from main_algo.CADENCE import make_observation, run_cadence


class StarterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cadence-x-path-")
        self.addCleanup(self.temp.cleanup)
        self.map = Path(self.temp.name) / "example_world.png"
        # Connected L with one visible turn and a two-cell-thick passage.
        free = {(x, y) for y in range(1, 7) for x in range(1, 3)}
        free |= {(x, y) for y in range(5, 7) for x in range(1, 7)}
        image = Image.new("L", (8, 8), 0)
        for point in free:
            image.putpixel(point, 255)
        image.save(self.map)
        prepare_map(self.map, backend="python")

    def test_native_matches_python_and_handles_x_in_paths(self):
        if not native_binary().is_file():
            self.skipTest("No native binary on this platform; Python fallback is tested separately")
        # Use the real generation entry point, which restores executable
        # permissions when an unzip utility has discarded Unix mode bits.
        shelf_path, backend = prepare_map(self.map, backend="native", force=True)
        self.assertEqual(backend, "native")
        with open_shelf(shelf_path) as shelf:
            actual = {key: shelf[key] for key in shelf if key != "metadata"}
        free, width, height = read_map(self.map)
        expected = json.loads(json.dumps(python_visibility(free, width, height)))
        self.assertEqual(json.loads(json.dumps(actual)), expected)

    def test_random_is_reproducible_and_student_starts_as_baseline(self):
        kwargs = dict(seed=17, deployment_point=(1, 1), quiet=True)
        first = run_cadence(self.map, **kwargs)
        second = run_cadence(self.map, **kwargs)
        student = run_cadence(self.map, policy="student", **kwargs)
        self.assertTrue(first["success"])
        self.assertEqual(first["trace"], second["trace"])
        self.assertEqual(first["trace"], student["trace"])
        self.assertEqual(first["peak_agents_including_depot"], first["teleport_steps"]+1)

    def test_policy_observes_only_known_cells_and_valid_candidates(self):
        observations = []

        def policy(candidates, observation, rng):
            self.assertFalse(hasattr(observation, "sensor"))
            self.assertFalse(hasattr(observation, "visibility_data"))
            self.assertLess(len(observation.observed_free), 20)
            self.assertFalse(observation.observed_free & observation.observed_walls)
            self.assertTrue(set(candidates) <= observation.observed_free)
            self.assertTrue(set(candidates) <= observation.distances.keys())
            self.assertFalse(set(candidates) & set(observation.agent_positions))
            self.assertEqual(tuple(sorted(candidates)), candidates)
            if observations:
                self.assertTrue(observations[-1] <= observation.observed_free)
            observations.append(observation.observed_free)
            return rng.choice(candidates)

        result = run_cadence(self.map, deployment_point=(1, 1), selector=policy, quiet=True)
        self.assertTrue(result["success"])
        self.assertTrue(observations)
        for row in result["trace"]:
            self.assertGreaterEqual(row["new_cells"], 0)
            self.assertIn(row["selected"], row["candidates_before"])

    def test_selection_does_not_query_future_visibility(self):
        sensor = Sensor(self.map)
        self.addCleanup(sensor.close)
        queries, original = [], sensor.visible_from

        def record(point):
            queries.append(point)
            return original(point)

        sensor.visible_from = record
        make_observation(sensor, [(1, 1)], 0)
        self.assertEqual(queries, [(1, 1)])

    def test_limits_and_invalid_policy_output(self):
        for limit_name, value, status in (("step_limit", 0, "step_limit"), ("max_agents", 1, "agent_limit")):
            result = run_cadence(self.map, deployment_point=(1, 1), quiet=True, **{limit_name: value})
            self.assertEqual(result["status"], status)
            self.assertFalse(result["success"])
            self.assertIsNone(result["steps_to_full_coverage"])
        with self.assertRaisesRegex(ValueError, "Policy returned"):
            run_cadence(self.map, deployment_point=(1, 1), selector=lambda *args: (0, 0), quiet=True)
        with self.assertRaisesRegex(ValueError, "not free"):
            run_cadence(self.map, deployment_point=(0, 0), quiet=True)

    def test_hole_exclusion_and_known_space_paths(self):
        free = {(x, y) for y in range(1, 8) for x in range(1, 8)} - {(3, 3), (3, 4), (4, 3), (4, 4)}
        corners = valid_corners(free, 9, 9)
        self.assertEqual(len(corners), 3)
        self.assertNotIn((2, 2), [r["target"] for r in corners])
        self.assertEqual(known_distances({(1, 1), (2, 1), (4, 1)}, (1, 1)), {(1, 1): 0, (2, 1): 1})

    def test_shelf_is_portable_and_read_only_during_runs(self):
        path = self.map.with_suffix(".shelf")
        before = {p.name: p.read_bytes() for p in self.map.parent.glob("*.shelf.*")}
        with open_shelf(path) as shelf:
            self.assertEqual(shelf["metadata"]["format_version"], 1)
        run_cadence(self.map, deployment_point=(1, 1), quiet=True)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.map.parent.glob("*.shelf.*")})

    def test_exactly_first_thirty_maps_retained(self):
        files = map_files()
        self.assertEqual(len(files), 30)
        self.assertEqual(files[0].name, "dungeon_12.png")
        self.assertEqual(files[-1].name, "dungeon_2154.png")


if __name__ == "__main__":
    unittest.main()
