import unittest
from unittest.mock import patch, MagicMock
import os
import pickle
import time

# Mock the entire 'rich' library
import sys
sys.modules['rich'] = MagicMock()
sys.modules['rich.console'] = MagicMock()
sys.modules['rich.table'] = MagicMock()
sys.modules['rich.panel'] = MagicMock()
sys.modules['rich.text'] = MagicMock()
sys.modules['rich.prompt'] = MagicMock()
sys.modules['rich.align'] = MagicMock()
sys.modules['rich.live'] = MagicMock()
sys.modules['rich.layout'] = MagicMock()
sys.modules['rich.box'] = MagicMock()

# Now we can import the class from the script
from passbot import PassBotEnterprise, ProgressState, InputProfile, STATE_VERSION

class TestPassBotResumeBug(unittest.TestCase):

    def setUp(self):
        """Set up a clean environment for each test."""
        self.output_filename = "test_dictionary.txt"
        self.progress_filename = "passbot_progress.pkl"
        self.cleanup_files()

    def tearDown(self):
        """Clean up files after each test."""
        self.cleanup_files()

    def cleanup_files(self):
        """Remove test-generated files."""
        if os.path.exists(self.output_filename):
            os.remove(self.output_filename)
        if os.path.exists(self.progress_filename):
            os.remove(self.progress_filename)

    @patch('passbot.MatrixUI.show_full_banner')
    @patch('builtins.input', MagicMock(side_effect=['test', '', '', '', '', 'n', '', 'test_dictionary.txt', 'full', 'n', 'n', 'n']))
    def test_resume_with_missing_output_file_triggers_fresh_start(self, mock_show_banner):
        """
        Verify that resuming with a progress file but no output file
        forces a fresh start.
        """
        # 1. Create a realistic-looking progress file that suggests work was done.
        input_profile = InputProfile(
            words=["test"],
            mobile_numbers=[],
            date_fragments=[],
            year_ranges=[],
            special_chars=[],
            number_patterns=[],
            output_filename=self.output_filename,
            generation_mode="full",
            use_underscore_separator=False,
            max_output_count=None,
            gzip_output=False,
            shard_every_million=False,
            strong_threshold=60.0,
        )

        progress_state = ProgressState(
            version=STATE_VERSION,
            phases_done={},
            idx_cursors={1: (2, 0, 0, 0)},
            total_generated=2,  # Critically, this is > 0
            start_time=time.time(),
            input_profile=input_profile.__dict__,
            strong_mode_filtered=0,
            checksum="dummy_checksum"
        )

        with open(self.progress_filename, "wb") as f:
            pickle.dump(progress_state, f)

        # Ensure the output file is missing.
        self.assertFalse(os.path.exists(self.output_filename))

        # 2. Instantiate PassBot and attempt to resume.
        app = PassBotEnterprise()

        # Mock the `_collect` method to prevent it from asking for input
        # when the resume fails and it tries to start fresh. We need to
        # control the input profile.
        app._collect = MagicMock(return_value=input_profile)

        # Mock `Confirm.ask` to automatically answer "yes" to the resume prompt.
        with patch('passbot.Confirm.ask', MagicMock(return_value=True)):
            # 3. Run the app.
            app.run()

        # 4. Assert that the final output is complete.
        # A complete run with the word "test" should generate "test", "TEST", "Test", etc.
        self.assertTrue(os.path.exists(self.output_filename))
        with open(self.output_filename, "r") as f:
            content = f.read()
            self.assertIn("test", content)
            self.assertIn("TEST", content)
            self.assertIn("Test", content)

if __name__ == '__main__':
    unittest.main()
