"""Tests for the OctoPrint client."""

import pytest
import sys
import os
import json
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from 3d_print_agent.octoprint_client import (
    OctoPrintClient,
    GCodeAnalyzer
)


class TestOctoPrintClient:
    """Tests for OctoPrintClient."""
    
    @patch('httpx.Client')
    def test_initialization(self, mock_client):
        """Test client initialization."""
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key',
            timeout=30.0
        )
        
        assert client.base_url == 'http://192.168.1.100:8080'
        assert client.api_key == 'test_api_key'
        assert client.timeout == 30.0
    
    @patch('httpx.Client')
    def test_connect_success(self, mock_client_class):
        """Test successful connection."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        
        result = client.connect()
        
        assert result is True
        assert client._connected is True
        mock_client.get.assert_called_once_with('/api/version')
    
    @patch('httpx.Client')
    def test_connect_failure(self, mock_client_class):
        """Test connection failure."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client
        
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        
        result = client.connect()
        
        assert result is False
        assert client._connected is False
    
    @patch('httpx.Client')
    def test_halt_print(self, mock_client_class):
        """Test print halting."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        client._connected = True
        
        result = client.halt_print()
        
        assert result is True
        mock_client.post.assert_called_once()
    
    @patch('httpx.Client')
    def test_pause_print(self, mock_client_class):
        """Test print pausing."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        client._connected = True
        
        result = client.pause_print()
        
        assert result is True
    
    @patch('httpx.Client')
    def test_resume_print(self, mock_client_class):
        """Test print resuming."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        client._connected = True
        
        result = client.resume_print()
        
        assert result is True
    
    @patch('httpx.Client')
    def test_send_gcode(self, mock_client_class):
        """Test sending G-Code commands."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        client._connected = True
        
        commands = ['G28', 'G1 X10 Y10']
        results = client.send_gcode(commands)
        
        assert len(results) == 2
        assert all(r.get('success') for r in results)
    
    def test_disconnect(self):
        """Test client disconnection."""
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        
        # Should not have a client initially
        assert client._client is None
        assert client._connected is False
    
    def test_is_connected_false_initially(self):
        """Test initial connection state."""
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        
        assert client.is_connected() is False


class TestGCodeAnalyzer:
    """Tests for GCodeAnalyzer."""
    
    def test_parse_simple_gcode(self):
        """Test parsing simple G-Code."""
        gcode = """
        ; Simple test print
        M104 S200
        M140 S60
        G1 Z0.2 E5
        G1 Z0.4 E10
        G1 Z0.6 E15
        """
        
        result = GCodeAnalyzer.parse_gcode(gcode)
        
        assert result['total_layers'] == 3
        assert result['total_lines'] >= 6
    
    def test_parse_gcode_no_z_moves(self):
        """Test parsing G-Code without Z moves."""
        gcode = """
        M104 S200
        G1 X10 Y10 E5
        G1 X20 Y10 E10
        """
        
        result = GCodeAnalyzer.parse_gcode(gcode)
        
        assert result['total_layers'] == 0
    
    def test_generate_layer_adjustment(self):
        """Test G-Code generation for layer adjustment."""
        commands = GCodeAnalyzer.generate_layer_adjustment_gcode(
            start_layer=10,
            end_layer=20,
            layer_height=0.2
        )
        
        assert len(commands) > 0
        assert any('M82' in cmd for cmd in commands)
        assert any('M204' in cmd for cmd in commands)
        assert any('G92 Z' in cmd for cmd in commands)
    
    def test_generate_commands_correct_count(self):
        """Test that correct number of commands are generated."""
        commands = GCodeAnalyzer.generate_layer_adjustment_gcode(
            start_layer=5,
            end_layer=7,
            layer_height=0.3
        )
        
        # Should have commands for layers 5, 6, 7
        g92_count = sum(1 for cmd in commands if 'G92 Z' in cmd)
        assert g92_count == 3


class TestIntegration:
    """Integration tests."""
    
    @patch('httpx.Client')
    def test_complete_workflow(self, mock_client_class):
        """Test complete client workflow."""
        mock_client = MagicMock()
        
        # Version endpoint
        version_response = MagicMock()
        version_response.status_code = 200
        version_response.json.return_value = {'version': '1.9.0'}
        mock_client.get.return_value = version_response
        
        # Print status endpoint
        status_response = MagicMock()
        status_response.status_code = 200
        status_response.json.return_value = {
            'name': 'Test Printer',
            'flags': {'printing': True, 'error': False}
        }
        mock_client.get.return_value = status_response
        
        mock_client_class.return_value = mock_client
        
        client = OctoPrintClient(
            base_url='http://192.168.1.100:8080',
            api_key='test_api_key'
        )
        
        # Connect
        assert client.connect() is True
        
        # Get status
        status = client.get_printer_status()
        assert 'name' in status
        
        # Get temperatures
        temps_response = MagicMock()
        temps_response.status_code = 200
        temps_response.json.return_value = {
            'temps': [
                {'actual': 20.5, 'target': 200, 'name': 'Nozzle'},
                {'actual': 60.0, 'target': 60, 'name': 'Bed'}
            ]
        }
        mock_client.get.return_value = temps_response
        
        temps = client.get_temperatures()
        assert 'temps' in temps
        
        # Disconnect
        client.disconnect()
        assert client._connected is False
