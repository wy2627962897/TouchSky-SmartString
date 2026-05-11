import unittest

from src.gesture_mapping.attitude_mapper import AttitudeMapper


class TestAttitudeMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = AttitudeMapper(
            max_tilt_angle=45.0,
            dead_zone=5.0,
            response_expo=1.0,
            command_smoothing=1.0,
            max_delta_per_tick=100,
        )

    def test_clutch_released_outputs_zero(self):
        cmds = self.mapper.map_to_commands([0.0, 0.0, 9.8], clutch_pressed=False)
        self.assertEqual(cmds, {"lr": 0, "fb": 0, "ud": 0, "yaw": 0})

    def test_dead_zone_outputs_zero(self):
        self.assertEqual(self.mapper._apply_dead_zone_and_scale(4.9), 0.0)
        self.assertEqual(self.mapper._apply_dead_zone_and_scale(-4.9), 0.0)

    def test_roll_and_pitch_saturate_to_100(self):
        # 极限右倾: roll ~ +90deg -> lr 应饱和到 100
        cmds_roll = self.mapper.map_to_commands([-9.8, 0.0, 0.0], clutch_pressed=True)
        self.assertEqual(cmds_roll["lr"], 100)

        # 极限前倾: pitch ~ -90deg -> fb 应饱和到 100
        cmds_pitch = self.mapper.map_to_commands([0.0, -9.8, 0.0], clutch_pressed=True)
        self.assertEqual(cmds_pitch["fb"], 100)

    def test_command_smoothing_lowers_first_step(self):
        mapper = AttitudeMapper(
            max_tilt_angle=45.0,
            dead_zone=5.0,
            response_expo=1.0,
            command_smoothing=0.5,
            max_delta_per_tick=20,
        )
        cmds = mapper.map_to_commands([-9.8, 0.0, 0.0], clutch_pressed=True)
        self.assertTrue(0 < cmds["lr"] < 100)


if __name__ == "__main__":
    unittest.main()
