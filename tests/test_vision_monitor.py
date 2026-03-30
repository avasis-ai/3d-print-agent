"""Tests for the vision monitoring system."""

import pytest
import sys
import os
import numpy as np
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from 3d_print_agent.vision_monitor import (
    FailureDetector,
    FailureType,
    WebcamSimulator
)


class TestFailureDetector:
    """Tests for FailureDetector."""
    
    @patch('cv2.VideoCapture')
    def test_initialization(self, mock_cap):
        """Test detector initialization."""
        detector = FailureDetector(
            camera_source=0,
            threshold=0.7,
            smoothing_window=5
        )
        
        assert detector.camera_source == 0
        assert detector.threshold == 0.7
        assert detector.smoothing_window == 5
        assert detector._connected is False
    
    @patch('cv2.VideoCapture')
    def test_connect_success(self, mock_cap):
        """Test successful camera connection."""
        mock_video = MagicMock()
        mock_video.isOpened.return_value = True
        mock_cap.return_value = mock_video
        
        detector = FailureDetector()
        result = detector.connect()
        
        assert result is True
        assert detector._connected is True
        mock_cap.assert_called_once_with(0)
    
    @patch('cv2.VideoCapture')
    def test_connect_failure(self, mock_cap):
        """Test camera connection failure."""
        mock_video = MagicMock()
        mock_video.isOpened.return_value = False
        mock_cap.return_value = mock_video
        
        detector = FailureDetector()
        result = detector.connect()
        
        assert result is False
        assert detector._connected is False
    
    @patch('cv2.VideoCapture')
    def test_disconnect(self, mock_cap):
        """Test camera disconnection."""
        mock_video = MagicMock()
        mock_video.isOpened.return_value = True
        mock_cap.return_value = mock_video
        
        detector = FailureDetector()
        detector.connect()
        
        assert detector._connected is True
        detector.disconnect()
        
        assert detector._connected is False
        mock_video.release.assert_called_once()
    
    def test_detect_failure_with_simulator(self):
        """Test failure detection using simulator."""
        detector = FailureDetector()
        detector._connected = True
        detector._cap = MagicMock()
        
        # Simulate normal frame
        normal_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        normal_frame[:, :] = [50, 50, 50]
        
        detector._cap.read.return_value = (True, normal_frame)
        
        # Run multiple detections to build smoothing window
        for _ in range(10):
            detector.detect_failure()
        
        status = detector.get_status()
        
        # Should not detect failure with normal frame
        assert status['failure_type'] in ['none', 'none']
        assert status['is_detected'] is False
    
    def test_smoothing_window(self):
        """Test temporal smoothing of results."""
        detector = FailureDetector(smoothing_window=3)
        
        # Feed results
        detector._last_results = [
            FailureType.NONE,
            FailureType.SPAGHETTI,
            FailureType.SPAGHETTI
        ]
        
        # Add one more
        result = detector._apply_smoothing(FailureType.SPAGHETTI)
        
        # Should return SPAGHETTI as most common
        assert result == FailureType.SPAGHETTI


class TestWebcamSimulator:
    """Tests for WebcamSimulator."""
    
    def test_normal_operation(self):
        """Test simulator with normal operation."""
        sim = WebcamSimulator(failure_type=None)
        
        frame = sim.generate_frame()
        
        assert frame.shape == (480, 640, 3)
        assert isinstance(frame, np.ndarray)
    
    def test_spaghetti_simulation(self):
        """Test spaghetti failure simulation."""
        sim = WebcamSimulator(failure_type=FailureType.SPAGHETTI)
        
        frame = sim.generate_frame()
        
        assert frame is not None
        assert frame.shape == (480, 640, 3)
        
        # Check that multiple colors were used
        unique_colors = len(np.unique(frame.reshape(-1, 3), axis=0))
        assert unique_colors > 1
    
    def test_temperature_anomaly_simulation(self):
        """Test temperature anomaly simulation."""
        sim = WebcamSimulator(failure_type=FailureType.TEMP_ANOMALY)
        
        frame = sim.generate_frame()
        
        assert frame is not None
        assert frame.shape == (480, 640, 3)


class TestIntegration:
    """Integration tests."""
    
    @patch('cv2.VideoCapture')
    def test_full_workflow(self, mock_cap):
        """Test complete monitoring workflow."""
        mock_video = MagicMock()
        mock_video.isOpened.return_value = True
        mock_video.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.return_value = mock_video
        
        detector = FailureDetector(camera_source=0, threshold=0.7)
        
        # Connect
        assert detector.connect() is True
        
        # Get status
        status = detector.get_status()
        assert 'failure_type' in status
        assert 'confidence' in status
        assert 'is_detected' in status
        
        # Disconnect
        detector.disconnect()
        assert detector._connected is False
