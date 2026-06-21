import sys
import inspect
import unittest
from pathlib import Path


ANIMATION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANIMATION_DIR))


class QonnectExplainerTests(unittest.TestCase):
    def test_bob_label_sits_outside_the_final_link(self) -> None:
        from manim import ORIGIN, RIGHT
        import qonnect_explainer

        self.assertIn(
            "label_direction",
            inspect.signature(qonnect_explainer.repeater).parameters,
        )

        bob = qonnect_explainer.repeater(
            "BOB",
            ORIGIN,
            endpoint=True,
            label_direction=RIGHT,
        )

        self.assertGreater(bob[1].get_left()[0], bob[0].get_right()[0])

    def test_correction_outcomes_fit_the_card(self) -> None:
        import qonnect_explainer

        self.assertTrue(hasattr(qonnect_explainer, "correction_outcomes"))

        outcomes = qonnect_explainer.correction_outcomes()

        self.assertEqual(outcomes.original_text, "00  01\n10  11")
        self.assertLessEqual(outcomes.width, 2.0)

    def test_each_major_panel_uses_the_extended_hold(self) -> None:
        import qonnect_explainer

        self.assertTrue(hasattr(qonnect_explainer, "panel_hold"))
        self.assertEqual(qonnect_explainer.panel_hold(1.0), 1.5)

        panel_methods = (
            "introduction",
            "board_mapping",
            "entanglement_generation",
            "entanglement_swapping",
            "physical_workflow",
            "probability_and_decay",
            "final_scope",
        )
        for method_name in panel_methods:
            method = getattr(qonnect_explainer.QonnectRepeaterExplainer, method_name)
            with self.subTest(panel=method_name):
                self.assertIn("self.wait(panel_hold(", inspect.getsource(method))

    def test_intro_copy_matches_requested_message(self) -> None:
        import qonnect_explainer

        self.assertEqual(getattr(qonnect_explainer, "INTRO_TITLE", None), "Qonnect")
        self.assertEqual(
            getattr(qonnect_explainer, "INTRO_SUBTITLE", None),
            "Extending quantum teleportation",
        )

    def test_first_log_replaces_goal_instructions_atomically(self) -> None:
        from manim import FadeIn, FadeOut, Succession, Text, VGroup
        import qonnect_explainer

        self.assertTrue(hasattr(qonnect_explainer, "action_log_transition"))

        goal_steps = VGroup(Text("goal"))
        first_log = Text("EG (R1,R2)")

        transition = qonnect_explainer.action_log_transition(goal_steps, first_log)

        self.assertIsInstance(transition, Succession)
        self.assertEqual(len(transition.animations), 2)
        self.assertIsInstance(transition.animations[0], FadeOut)
        self.assertIs(transition.animations[0].mobject, goal_steps)
        self.assertIsInstance(transition.animations[1], FadeIn)
        self.assertIs(transition.animations[1].mobject, first_log)

    def test_board_mapping_uses_atomic_first_log_transition(self) -> None:
        from qonnect_explainer import QonnectRepeaterExplainer

        source = inspect.getsource(QonnectRepeaterExplainer.board_mapping)

        self.assertIn("action_log_transition(self.goal_steps, first_log)", source)

    def test_storyboard_covers_gameplay_and_repeater_physics(self) -> None:
        from qonnect_explainer import STORY_BEATS

        self.assertEqual(
            STORY_BEATS,
            (
                "game_board_mapping",
                "entanglement_generation",
                "entanglement_swapping",
                "end_to_end_link",
                "probability_and_decay",
                "physical_scope",
            ),
        )

    def test_palette_matches_qonnect(self) -> None:
        from qonnect_explainer import CYAN, GREEN, AMBER, BACKGROUND

        self.assertEqual(CYAN, "#00E6DC")
        self.assertEqual(GREEN, "#3CFF82")
        self.assertEqual(AMBER, "#FFB020")
        self.assertEqual(BACKGROUND, "#06080A")

    def test_swap_rule_uses_the_shared_repeater(self) -> None:
        from qonnect_explainer import SWAP_RULE

        self.assertEqual(SWAP_RULE, "(i,j) + (j,k) → (i,k)")

    def test_physical_scope_names_required_operations(self) -> None:
        from qonnect_explainer import PHYSICAL_SCOPE

        self.assertIn("Bell-state measurement", PHYSICAL_SCOPE)
        self.assertIn("classical", PHYSICAL_SCOPE)
        self.assertIn("memory", PHYSICAL_SCOPE)

    def test_scene_is_a_manim_scene(self) -> None:
        from manim import Scene
        from qonnect_explainer import QonnectRepeaterExplainer

        self.assertTrue(issubclass(QonnectRepeaterExplainer, Scene))


if __name__ == "__main__":
    unittest.main()
