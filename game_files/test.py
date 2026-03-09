import unittest
import pygame
import sys
import os
from unittest.mock import Mock, patch
from game import Qonnect

class TestQonnectGame(unittest.TestCase):
    
    def setUp(self):
        """Set up a test game instance before each test"""
        # Mock pygame.display.set_mode to avoid opening windows during tests
        self.original_set_mode = pygame.display.set_mode
        pygame.display.set_mode = Mock(return_value=Mock())
        
        self.config = {
             'grid_size': 5,
            'cell_size': 80,
            'padding': 1,
            'bg_color': (240, 240, 240),
            'grid_color': (200, 200, 200),
            'dot_color': (255, 100, 100),
            'target_color': (100, 255, 100),
            'merge_enabled': True,
            'window_title': "Qonnect Test",
            'diagonal_color': (255, 0, 0),
            'text_color': (0, 0, 0),
            'text_padding': 20,
            'dot_lifetime': 5,
            'title_font_size': 48,
            'selection_color': (100, 200, 255),
            'selection_thickness': 5,
            'dot_creation_prob': 1.0,  # Use 1.0 for deterministic testing
            'dot_merge_prob': 1.0,     # Use 1.0 for deterministic testing
        }
        
        self.game = Qonnect(self.config)
    
    def tearDown(self):
        """Clean up after each test"""
        pygame.display.set_mode = self.original_set_mode
        if hasattr(self, 'game'):
            del self.game
    
    def test_initialization(self):
        """Test that the game initializes correctly with different parameters"""
        test_configs = [
            {'grid_size': 3, 'dot_lifetime': 3, 'dot_creation_prob': 0.5},
            {'grid_size': 4, 'dot_lifetime': 10, 'dot_creation_prob': 0.8},
            {'grid_size': 6, 'dot_lifetime': 7, 'dot_merge_prob': 0.9},
        ]
        
        for config in test_configs:
            with self.subTest(**config):
                test_config = self.config.copy()
                test_config.update(config)
                
                game = Qonnect(test_config)
                
                self.assertEqual(game.config['grid_size'], config['grid_size'])
                self.assertEqual(game.config['dot_lifetime'], config['dot_lifetime'])
                self.assertEqual(len(game.grid), config['grid_size'])
                self.assertEqual(len(game.grid[0]), config['grid_size'])
                self.assertFalse(game.game_over)
                self.assertFalse(game.win)
                self.assertEqual(game.action_count, 0)
    
    def test_special_cells_initialization(self):
        """Test that black and grey cells are initialized correctly for different grid sizes"""
        sizes = [3, 4, 5, 6]
        
        for size in sizes:
            with self.subTest(grid_size=size):
                config = self.config.copy()
                config['grid_size'] = size
                game = Qonnect(config)
                
                # Test black cells (main diagonal)
                expected_black_cells = [(i, i) for i in range(size)]
                self.assertEqual(game.config['black_cells'], expected_black_cells)
                
                # Test grey cells (adjacent to diagonal)
                for i in range(size):
                    if i + 1 < size:
                        self.assertIn((i, i + 1), game.config['grey_cells'])
                    if i - 1 >= 0:
                        self.assertIn((i, i - 1), game.config['grey_cells'])
    
    def test_target_position(self):
        """Test that target position is set correctly"""
        sizes = [3, 4, 5]
        
        for size in sizes:
            with self.subTest(grid_size=size):
                config = self.config.copy()
                config['grid_size'] = size
                game = Qonnect(config)
                
                expected_target = (0, size - 1)
                self.assertEqual(game.config['target_position'], expected_target)
    
    def test_pos_to_grid_conversion(self):
        """Test screen position to grid coordinate conversion"""
        # Mock positions for a 5x5 grid
        test_cases = [
            # (screen_x, screen_y, expected_grid_pos)
            (25, 60, (0, 0)),   # Top-left cell
            (105, 60, (0, 1)),  # Top row, second cell
            (25, 140, (1, 0)),  # Second row, first cell
            (500, 500, None),   # Outside grid
            (10, 50, None),     # Outside grid (left of numbers)
        ]
        
        for screen_x, screen_y, expected in test_cases:
            with self.subTest(x=screen_x, y=screen_y):
                result = self.game.pos_to_grid((screen_x, screen_y))
                self.assertEqual(result, expected)
    
    def test_valid_placement_positions(self):
        """Test that only grey cells are valid for placement"""
        # For a 5x5 grid, grey cells should be adjacent to diagonal
        valid_positions = [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3)]
        invalid_positions = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4),  # Black cells
                           (0, 2), (2, 0), (1, 3), (3, 1)]  # Non-adjacent cells
        
        for pos in valid_positions:
            with self.subTest(pos=pos, expected=True):
                self.assertTrue(self.game.is_valid_placement_position(*pos))
        
        for pos in invalid_positions:
            with self.subTest(pos=pos, expected=False):
                self.assertFalse(self.game.is_valid_placement_position(*pos))
    
    def test_dot_placement_deterministic(self):
        """Test dot placement with probability 1.0 (deterministic)"""
        valid_position = (0, 1)  # A valid grey cell
        
        # Test successful placement
        success = self.game.place_dot_with_symmetry(*valid_position)
        self.assertTrue(success)
        self.assertTrue(self.game.grid[0][1])  # Original position
        self.assertTrue(self.game.grid[1][0])  # Mirror position
        self.assertEqual(self.game.dot_timers[(0, 1)], self.config['dot_lifetime'])
        self.assertEqual(self.game.dot_timers[(1, 0)], self.config['dot_lifetime'])
        self.assertEqual(self.game.action_count, 1)
    
    def test_dot_placement_probabilistic(self):
        """Test dot placement with different probabilities"""
        probabilities = [0.0, 0.5, 1.0]
        n_tests = 50
        
        for prob in probabilities:
            with self.subTest(probability=prob):
                config = self.config.copy()
                config['dot_creation_prob'] = prob
                game = Qonnect(config)
                
                success_count = 0
                for _ in range(n_tests):
                    game.grid = [[False for _ in range(5)] for _ in range(5)]
                    game.dot_timers = {}
                    if game.place_dot_with_symmetry(0, 1):
                        success_count += 1
                
                success_rate = success_count / n_tests
                tolerance = 0.15
                self.assertAlmostEqual(success_rate, prob, delta=tolerance)
    
    def test_dot_placement_invalid_position(self):
        """Test that dots cannot be placed on invalid positions"""
        invalid_positions = [(0, 0), (1, 1), (2, 2)]  # Black cells
        
        for pos in invalid_positions:
            with self.subTest(pos=pos):
                success = self.game.place_dot_with_symmetry(*pos)
                self.assertFalse(success)
                self.assertFalse(self.game.grid[pos[0]][pos[1]])
    
    def test_dot_merging_valid(self):
        """Test valid dot merging scenarios"""
        # Test case: (0,1) and (1,2) should merge to (0,2)
        self.game.place_dot_with_symmetry(0, 1)
        self.game.place_dot_with_symmetry(1, 2)
        
        # Reset action count for clean test
        self.game.action_count = 0
        
        # Perform merge
        self.game.merge_dots_with_symmetry((0, 1), (1, 2))
        
        # Check results
        self.assertFalse(self.game.grid[0][1])  # Original dots removed
        self.assertFalse(self.game.grid[1][0])
        self.assertFalse(self.game.grid[1][2])
        self.assertFalse(self.game.grid[2][1])
        self.assertTrue(self.game.grid[0][2])   # New dot created
        self.assertTrue(self.game.grid[2][0])   # Mirror dot created
        self.assertEqual(self.game.action_count, 1)
    
    def test_dot_merging_invalid(self):
        """Test that mirror positions cannot be merged"""
        self.game.place_dot_with_symmetry(0, 1)
        
        # Try to merge with mirror position (should not work)
        self.game.merge_dots_with_symmetry((0, 1), (1, 0))
        
        # Dots should still exist
        self.assertTrue(self.game.grid[0][1])
        self.assertTrue(self.game.grid[1][0])
    
    def test_dot_merging_probabilistic(self):
        """Test dot merging with different probabilities"""
        probabilities = [0.0, 0.5, 1.0]
        n_tests = 30
        
        for prob in probabilities:
            with self.subTest(probability=prob):
                config = self.config.copy()
                config['dot_merge_prob'] = prob
                game = Qonnect(config)
                
                success_count = 0
                for _ in range(n_tests):
                    # Reset game state
                    game.grid = [[False for _ in range(5)] for _ in range(5)]
                    game.dot_timers = {}
                    
                    # Place two dots
                    game.place_dot_with_symmetry(0, 1)
                    game.place_dot_with_symmetry(1, 2)
                    
                    # Try to merge
                    initial_dot_count = sum(sum(row) for row in game.grid)
                    game.merge_dots_with_symmetry((0, 1), (1, 2))
                    final_dot_count = sum(sum(row) for row in game.grid)
                    
                    # If merge was successful, dot count should change
                    if final_dot_count != initial_dot_count:
                        success_count += 1
                
                success_rate = success_count / n_tests
                tolerance = 0.2
                self.assertAlmostEqual(success_rate, prob, delta=tolerance)
    
    def test_dot_aging(self):
        """Test that dots age and disappear after their lifetime"""
        self.game.place_dot_with_symmetry(0, 1)
        initial_lifetime = self.game.dot_timers[(0, 1)]
        
        # Age dots multiple times
        for i in range(initial_lifetime):
            self.game.age_dots()
            self.assertEqual(self.game.dot_timers[(0, 1)], initial_lifetime - i - 1)
        
        # Dot should be removed after lifetime expires
        self.game.age_dots()
        self.assertNotIn((0, 1), self.game.dot_timers)
        self.assertFalse(self.game.grid[0][1])
        self.assertFalse(self.game.grid[1][0])
    
    def test_win_condition(self):
        """Test that win condition is detected correctly"""
        # Manually place dot in target position
        target_pos = self.game.config['target_position']
        self.game.grid[target_pos[0]][target_pos[1]] = True
        
        self.game.check_win_condition()
        
        self.assertTrue(self.game.game_over)
        self.assertTrue(self.game.win)
    
    def test_win_condition_mirror(self):
        """Test that win condition works for mirror position too"""
        target_pos = self.game.config['target_position']
        mirror_pos = (target_pos[1], target_pos[0])  # Mirror of target
        
        self.game.grid[mirror_pos[0]][mirror_pos[1]] = True
        
        self.game.check_win_condition()
        
        self.assertTrue(self.game.game_over)
        self.assertTrue(self.game.win)
    
    def test_action_logging(self):
        """Test that actions are properly logged"""
        test_actions = [
            "Entangle (1,2)",
            "Swap (1,2) and (2,3)",
            "Entangle (3,4)"
        ]
        
        for action in test_actions:
            self.game.log_action(action)
        
        self.assertEqual(len(self.game.action_log), len(test_actions))
        self.assertEqual(self.game.action_log, test_actions)
    
    def test_can_merge_check(self):
        """Test the can_merge validation"""
        # Valid merges (not mirrors)
        valid_pairs = [
            ((0, 1), (1, 2)),  # Different positions
            ((0, 1), (2, 3)),  # Different positions
        ]
        
        # Invalid merges (mirrors)
        invalid_pairs = [
            ((0, 1), (1, 0)),  # Mirror positions
            ((2, 3), (3, 2)),  # Mirror positions
        ]
        
        for pos1, pos2 in valid_pairs:
            with self.subTest(pos1=pos1, pos2=pos2, expected=True):
                self.assertTrue(self.game.can_merge(pos1, pos2))
        
        for pos1, pos2 in invalid_pairs:
            with self.subTest(pos1=pos1, pos2=pos2, expected=False):
                self.assertFalse(self.game.can_merge(pos1, pos2))

class TestQonnectIntegration(unittest.TestCase):
    """Integration tests for the complete game workflow"""
    
    def setUp(self):
        pygame.display.set_mode = Mock(return_value=Mock())
        self.config = {
            'grid_size': 4,
            'cell_size': 80,
            'dot_lifetime': 3,
            'dot_creation_prob': 1.0,
            'dot_merge_prob': 1.0,
            'merge_enabled': True,
        }
        self.game = Qonnect(self.config)
    
    def test_complete_game_workflow(self):
        """Test a complete game workflow from start to win"""
        # Step 1: Place initial dots
        self.game.place_dot_with_symmetry(0, 1)  # Creates (0,1) and (1,0)
        self.game.place_dot_with_symmetry(1, 2)  # Creates (1,2) and (2,1)
        
        # Verify initial state
        self.assertTrue(self.game.grid[0][1])
        self.assertTrue(self.game.grid[1][0])
        self.assertTrue(self.game.grid[1][2])
        self.assertTrue(self.game.grid[2][1])
        self.assertEqual(self.game.action_count, 2)
        
        # Step 2: Merge to create longer link
        self.game.merge_dots_with_symmetry((0, 1), (1, 2))  # Should create (0,2) and (2,0)
        
        # Verify merge results
        self.assertFalse(self.game.grid[0][1])  # Original dots removed
        self.assertFalse(self.game.grid[1][2])
        self.assertTrue(self.game.grid[0][2])   # New link created
        self.assertTrue(self.game.grid[2][0])   # Mirror link created
        self.assertEqual(self.game.action_count, 3)
        
        # Step 3: Place another dot and merge to reach target
        self.game.place_dot_with_symmetry(2, 3)  # Creates (2,3) and (3,2)
        self.game.merge_dots_with_symmetry((0, 2), (2, 3))  # Should create (0,3) - THE TARGET!
        
        # Verify win condition
        self.assertTrue(self.game.game_over)
        self.assertTrue(self.game.win)
        self.assertTrue(self.game.grid[0][3])  # Target position has dot
    
    def test_game_reset(self):
        """Test that game can be reset properly"""
        # Play some moves
        self.game.place_dot_with_symmetry(0, 1)
        self.game.place_dot_with_symmetry(1, 2)
        
        # Reset game
        original_config = self.game.config.copy()
        self.game.__init__(self.config)
        
        # Verify reset state
        self.assertFalse(self.game.game_over)
        self.assertFalse(self.game.win)
        self.assertEqual(self.game.action_count, 0)
        
        # Grid should be empty
        for row in self.game.grid:
            for cell in row:
                self.assertFalse(cell)
        
        # Dot timers should be empty
        self.assertEqual(len(self.game.dot_timers), 0)

class TestQonnectEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        pygame.display.set_mode = Mock(return_value=Mock())
        self.config = {
            'grid_size': 3,  # Small grid for edge case testing
            'cell_size': 80,
            'dot_lifetime': 2,
            'dot_creation_prob': 1.0,
            'dot_merge_prob': 1.0,
            'merge_enabled': True,
        }
        self.game = Qonnect(self.config)
    
    def test_small_grid_operations(self):
        """Test game operations on a small grid"""
        # For 3x3 grid, target is (0,2)
        self.assertEqual(self.game.config['target_position'], (0, 2))
        
        # Test valid placements
        valid_placements = [(0, 1), (1, 0), (1, 2), (2, 1)]
        for pos in valid_placements:
            with self.subTest(pos=pos):
                success = self.game.place_dot_with_symmetry(*pos)
                self.assertTrue(success)
    
    def test_boundary_merging(self):
        """Test merging at grid boundaries"""
        # Create a chain that reaches the boundary
        self.game.place_dot_with_symmetry(0, 1)
        self.game.place_dot_with_symmetry(1, 2)
        
        # Merge should work normally
        self.game.merge_dots_with_symmetry((0, 1), (1, 2))
        self.assertTrue(self.game.grid[0][2])  # Should create dot at (0,2) - the target!
        
        # Game should be won
        self.assertTrue(self.game.game_over)
        self.assertTrue(self.game.win)
    
    def test_dot_lifetime_zero(self):
        """Test behavior with zero lifetime"""
        config = self.config.copy()
        config['dot_lifetime'] = 0
        game = Qonnect(config)
        
        # Place a dot - it should immediately disappear
        game.place_dot_with_symmetry(0, 1)
        self.assertFalse(game.grid[0][1])
        self.assertFalse(game.grid[1][0])
        self.assertEqual(len(game.dot_timers), 0)

def run_game_tests():
    """Run all game tests with detailed reporting"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestQonnectGame))
    suite.addTests(loader.loadTestsFromTestCase(TestQonnectIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestQonnectEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"QONNECT GAME TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print(f"{'='*60}")
    
    if result.wasSuccessful():
        print("🎮 All game tests passed!")
    else:
        print("❌ Some game tests failed..")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running Qonnect Game Tests...")
    print("Testing game mechanics, rules, and edge cases...")
    print("=" * 60)
    
    # Set SDL video driver to dummy for headless testing
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    
    success = run_game_tests()
    
    exit(0 if success else 1)