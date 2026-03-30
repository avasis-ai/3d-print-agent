"""Tests for the CLI interface."""

import pytest
import sys
import os
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from 3d_print_agent.cli import (
    main,
    monitor,
    octoprint,
    analyze,
    adjust,
    test
)


class TestCLI:
    """Tests for CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(main, ['--version'])
        
        assert result.exit_code == 0
        assert "version" in result.output.lower()
        assert "0.1.0" in result.output
    
    def test_help_command(self):
        """Test help output."""
        result = self.runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "3D-Print-Agent" in result.output
        assert "monitor" in result.output
        assert "octoprint" in result.output
    
    @patch('3d_print_agent.cli.FailureDetector')
    def test_monitor_command(self, mock_detector_class):
        """Test monitor command."""
        mock_detector = MagicMock()
        mock_detector.connect.return_value = True
        mock_detector.get_status.return_value = {
            'failure_type': 'none',
            'confidence': 0.1,
            'is_detected': False,
            'camera_connected': True,
            'last_update': 1234567890.0
        }
        mock_detector_class.return_value = mock_detector
        
        # Simulate Ctrl+C
        with pytest.raises(SystemExit):
            result = self.runner.invoke(monitor, ['--camera', '0', '--threshold', '0.7'])
        
        # Check that we got monitoring output
        assert "Connected to camera" in result.output
        assert "Monitoring stopped" in result.output
    
    @patch('3d_print_agent.cli.OctoPrintClient')
    def test_octoprint_command(self, mock_client_class):
        """Test OctoPrint command."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        
        # Get status response
        mock_status = MagicMock()
        mock_status.get_printer_status.return_value = {
            'name': 'Test Printer',
            'flags': {'printing': True}
        }
        
        # Get temperatures response
        mock_temps = MagicMock()
        mock_temps.get_temperatures.return_value = {
            'temps': [
                {'bedActual': 60.0, 'bedTarget': 60}
            ]
        }
        
        mock_client_class.return_value = mock_client
        
        result = self.runner.invoke(octoprint, [
            '--octoprint-url', 'http://192.168.1.100:8080',
            '--api-key', 'test_key'
        ])
        
        assert result.exit_code == 0
        assert "Connected to" in result.output
    
    @patch('builtins.open')
    def test_analyze_command(self, mock_open):
        """Test analyze command."""
        from io import StringIO
        import yaml
        
        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock()
        mock_file.read.return_value = yaml.dump({
            'gcode': '; Test G-Code\nG1 Z0.2\nG1 Z0.4\nG1 Z0.6'
        })
        mock_open.return_value = mock_file
        
        result = self.runner.invoke(analyze, ['--config', 'test.yaml'])
        
        assert result.exit_code == 0
        assert "Total lines" in result.output
    
    def test_adjust_command(self):
        """Test adjust command."""
        result = self.runner.invoke(adjust, [
            '--layers', '10:20',
            '--height', '0.25'
        ])
        
        assert result.exit_code == 0
        assert "Generated G-Code" in result.output
        assert "Layer 10" in result.output
    
    def test_adjust_command_invalid(self):
        """Test adjust command with invalid input."""
        result = self.runner.invoke(adjust, ['--layers', 'invalid', '--height', '0.2'])
        
        assert result.exit_code != 0
        assert "Invalid layer range" in result.output
    
    @patch('3d_print_agent.cli.WebcamSimulator')
    def test_test_command(self, mock_sim):
        """Test test command."""
        mock_sim.return_value = MagicMock()
        mock_sim.return_value.get_status.return_value = {
            'failure_type': 'none',
            'frames_generated': 10,
            'is_simulated': True
        }
        
        result = self.runner.invoke(test)
        
        assert result.exit_code == 0
        assert "All tests passed!" in result.output


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_all_commands_available(self):
        """Test that all expected commands are available."""
        result = self.runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "monitor" in result.output
        assert "octoprint" in result.output
        assert "analyze" in result.output
        assert "adjust" in result.output
        assert "test" in result.output
    
    def test_version_output_format(self):
        """Test that version output is correct format."""
        result = self.runner.invoke(main, ['--version'])
        
        assert "3d-print-agent" in result.output
        assert "0.1.0" in result.output
