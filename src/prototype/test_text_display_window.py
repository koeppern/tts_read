#!/usr/bin/env python3
"""
Test file for TextDisplayWindow functionality.
"""

import sys
import os
import unittest
import tkinter as tk
from unittest.mock import Mock, patch
import time

# Add src directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from settings_manager import SettingsManager
from text_display_window import TextDisplayWindow


class TestTextDisplayWindow(unittest.TestCase):
	"""Test cases for TextDisplayWindow."""
	
	def setUp(self):
		"""Set up test fixtures."""
		self.settings_manager = Mock(spec=SettingsManager)
		self.settings_manager.get_setting.return_value = 16  # Default font size
		self.settings_manager.save_setting = Mock()
		
		# Create display window
		self.display_window = TextDisplayWindow(self.settings_manager)
		
	def tearDown(self):
		"""Clean up after tests."""
		if (
			self.display_window.window 
			and self.display_window.window.winfo_exists()
		):
			self.display_window.window.destroy()
			
	def test_initialization(self):
		"""Test that TextDisplayWindow initializes correctly."""
		self.assertIsInstance(self.display_window, TextDisplayWindow)
		self.assertEqual(self.display_window.current_text, "")
		self.assertTrue(self.display_window.is_autoscroll_enabled)
		self.assertIsNone(self.display_window.window)
		
	def test_create_window(self):
		"""Test window creation."""
		self.display_window.create_window()
		
		self.assertIsNotNone(self.display_window.window)
		self.assertIsNotNone(self.display_window.text_widget)
		self.assertTrue(self.display_window.window.winfo_exists())
		
		# Test window properties
		self.assertEqual(self.display_window.window.title(), "Vorgelesener Text")
		
	def test_set_text(self):
		"""Test setting text in the window."""
		test_text = "Dies ist ein Test-Text für das Vorlese-Fenster."
		
		self.display_window.set_text(test_text)
		
		# Window should be created automatically
		self.assertIsNotNone(self.display_window.window)
		self.assertEqual(self.display_window.current_text, test_text)
		
		# Text should be in the widget
		widget_text = self.display_window.text_widget.get("1.0", tk.END).strip()
		self.assertEqual(widget_text, test_text)
		
	def test_show_hide_window(self):
		"""Test showing and hiding the window."""
		# Initially no window
		self.assertIsNone(self.display_window.window)
		
		# Show should create window
		self.display_window.show()
		self.assertIsNotNone(self.display_window.window)
		self.assertTrue(self.display_window.window.winfo_exists())
		
		# Hide should withdraw window
		self.display_window.hide()
		# Window still exists but is withdrawn
		self.assertTrue(self.display_window.window.winfo_exists())
		
	def test_highlight_word(self):
		"""Test word highlighting functionality."""
		test_text = "Dies ist ein Test-Text für das Vorlese-Fenster."
		self.display_window.set_text(test_text)
		
		# Test highlighting first word "Dies" (location=0, length=4)
		self.display_window.highlight_word(0, 4)
		
		# Check that highlight tag exists
		highlight_ranges = self.display_window.text_widget.tag_ranges("highlight")
		self.assertTrue(len(highlight_ranges) > 0)
		
		# Test highlighting middle word "Test-Text" (location=13, length=9)
		self.display_window.highlight_word(13, 9)
		
		# Should still have highlight (previous one removed)
		highlight_ranges = self.display_window.text_widget.tag_ranges("highlight")
		self.assertTrue(len(highlight_ranges) > 0)
		
	def test_font_size_adjustment(self):
		"""Test font size increase and decrease."""
		self.display_window.create_window()
		
		# Get initial font size
		initial_font = self.display_window.text_widget.cget("font")
		
		# Test increase
		self.display_window.increase_font_size()
		
		# Test decrease 
		self.display_window.decrease_font_size()
		
		# Font should be adjusted (just test that no exception occurs)
		self.assertIsNotNone(self.display_window.text_widget.cget("font"))
		
	def test_autoscroll_enable_disable(self):
		"""Test autoscroll functionality."""
		self.display_window.create_window()
		
		# Initially enabled
		self.assertTrue(self.display_window.is_autoscroll_enabled)
		
		# Disable
		self.display_window.disable_autoscroll()
		self.assertFalse(self.display_window.is_autoscroll_enabled)
		
		# Enable
		self.display_window.enable_autoscroll()
		self.assertTrue(self.display_window.is_autoscroll_enabled)
		
	def test_on_close_saves_font_size(self):
		"""Test that closing the window saves font size."""
		self.display_window.create_window()
		
		# Simulate closing
		self.display_window.on_close()
		
		# Should have called save_setting
		self.settings_manager.save_setting.assert_called()
		
	def test_highlight_word_without_window(self):
		"""Test that highlighting without window doesn't crash."""
		# Should not raise exception
		self.display_window.highlight_word(0, 5)
		
	def test_multiple_show_calls(self):
		"""Test that multiple show calls don't create multiple windows."""
		self.display_window.show()
		first_window = self.display_window.window
		
		self.display_window.show()
		second_window = self.display_window.window
		
		# Should be the same window
		self.assertEqual(first_window, second_window)
		

class TestIntegration(unittest.TestCase):
	"""Integration tests for text display with TTS."""
	
	def setUp(self):
		"""Set up integration test fixtures."""
		self.settings_manager = Mock(spec=SettingsManager)
		self.settings_manager.get_setting.return_value = 16
		self.settings_manager.save_setting = Mock()
		
		self.display_window = TextDisplayWindow(self.settings_manager)
		
	def tearDown(self):
		"""Clean up after tests."""
		if (
			self.display_window.window 
			and self.display_window.window.winfo_exists()
		):
			self.display_window.window.destroy()
			
	def test_word_callback_simulation(self):
		"""Test simulated word boundary callbacks."""
		test_text = "Hello world from the text-to-speech system."
		self.display_window.set_text(test_text)
		
		# Simulate word boundary callbacks like TTS would send
		word_boundaries = [
			(0, 5),   # "Hello"
			(6, 5),   # "world" 
			(12, 4),  # "from"
			(17, 3),  # "the"
			(21, 12), # "text-to-speech"
			(34, 6),  # "system"
		]
		
		for location, length in word_boundaries:
			self.display_window.highlight_word(location, length)
			
			# Verify highlight exists
			highlight_ranges = (
				self.display_window.text_widget.tag_ranges("highlight")
			)
			self.assertTrue(len(highlight_ranges) > 0)
			
			# Small delay to simulate real-time speech
			time.sleep(0.01)
			
	def test_long_text_handling(self):
		"""Test handling of long text with many words."""
		# Create a longer test text
		long_text = " ".join(["Word" + str(i) for i in range(100)])
		
		self.display_window.set_text(long_text)
		
		# Test highlighting words throughout the text
		for i in range(0, len(long_text), 10):
			self.display_window.highlight_word(i, 5)
			
		# Should complete without errors
		self.assertTrue(True)
		

def run_visual_test():
	"""Run a visual test to see the window in action."""
	print("🧪 Running visual test of TextDisplayWindow...")
	
	# Create a real settings manager
	settings_manager = Mock()
	settings_manager.get_setting.return_value = 18
	settings_manager.save_setting = Mock()
	
	# Create display window
	display_window = TextDisplayWindow(settings_manager)
	
	# Set test text
	test_text = (
		"Dies ist ein Test des Folge-Text-Fensters. "
		"Es sollte den Text anzeigen und Wörter hervorheben, "
		"während der Text vorgelesen wird. Das Fenster kann "
		"mit verschiedenen Tastenkombinationen gesteuert werden."
	)
	
	display_window.set_text(test_text)
	display_window.show()
	
	print("✅ Visual test window created. Testing word highlighting...")
	
	# Simulate word highlighting
	words = test_text.split()
	position = 0
	
	for word in words:
		try:
			display_window.highlight_word(position, len(word))
			position += len(word) + 1  # +1 for space
			
			# Update window and wait
			display_window.update()
			time.sleep(0.5)
			
		except Exception as e:
			print(f"❌ Error highlighting word '{word}': {e}")
			break
			
	print("✅ Word highlighting test completed.")
	print("🎯 Window will stay open for manual testing.")
	print("   Test font size with Ctrl+Plus/Minus")
	print("   Test autoscroll with Space key")
	print("   Close with Ctrl+Q or window close button")
	
	# Keep window open for manual testing
	try:
		while display_window.window and display_window.window.winfo_exists():
			display_window.update()
			time.sleep(0.1)
	except tk.TclError:
		pass
		
	print("👋 Visual test completed.")


if __name__ == "__main__":
	import argparse
	
	parser = argparse.ArgumentParser(description="Test TextDisplayWindow")
	parser.add_argument(
		"--visual", 
		action="store_true", 
		help="Run visual test"
	)
	args = parser.parse_args()
	
	if args.visual:
		run_visual_test()
	else:
		print("🧪 Running TextDisplayWindow unit tests...")
		unittest.main(verbosity=2, exit=False)
		print("✅ All tests completed!") 