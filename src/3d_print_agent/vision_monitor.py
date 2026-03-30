"""Vision-based failure detection for 3D printing."""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
import time


class FailureType(Enum):
    """Types of 3D printing failures."""
    SPAGHETTI = "spaghetti_failure"
    TEMP_ANOMALY = "temperature_anomaly"
    DETACHMENT = "layer_detach"
    WARPING = "warping"
    EXTRUSION_ERROR = "extrusion_error"
    NONE = "none"


class FailureDetector:
    """Vision-based detection of 3D printing failures."""
    
    def __init__(
        self,
        camera_source: int = 0,
        threshold: float = 0.7,
        smoothing_window: int = 5
    ):
        """
        Initialize the failure detector.
        
        Args:
            camera_source: Camera device index (0 for default webcam)
            threshold: Detection confidence threshold (0.0-1.0)
            smoothing_window: Number of frames to average for smoothing
        """
        self.camera_source = camera_source
        self.threshold = threshold
        self.smoothing_window = smoothing_window
        self._last_results: List[FailureType] = []
        self._frame_count = 0
        
        # Initialize camera
        self._cap: Optional[cv2.VideoCapture] = None
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to the camera."""
        try:
            self._cap = cv2.VideoCapture(self.camera_source)
            if not self._cap.isOpened():
                return False
            
            # Set camera properties
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self._cap.set(cv2.CAP_PROP_FPS, 30)
            
            self._connected = True
            return True
        except Exception:
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the camera."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._connected = False
    
    def _apply_smoothing(self, result: FailureType) -> FailureType:
        """Apply temporal smoothing to detection results."""
        self._last_results.append(result)
        if len(self._last_results) > self.smoothing_window:
            self._last_results.pop(0)
        
        # Return most common result
        counts: Dict[FailureType, int] = {f: 0 for f in FailureType}
        for r in self._last_results:
            counts[r] += 1
        
        return max(counts, key=counts.get)
    
    def _detect_spaghetti(self, frame: np.ndarray) -> float:
        """
        Detect spaghetti failure (over-extrusion, tangled filament).
        
        Args:
            frame: Current camera frame
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define range for filament colors (commonly PLA/ABS colors)
        # This is simplified - in production would use trained models
        lower_pla = np.array([0, 50, 50])
        upper_pla = np.array([20, 255, 255])
        mask1 = cv2.inRange(hsv, lower_pla, upper_pla)
        
        # Detect excess filament patterns
        edges = cv2.Canny(frame, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(
            mask1 | edges, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Analyze contour complexity
        total_area = 0
        complexity_score = 0.0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small noise
                total_area += area
                
                # Calculate circularity (0 = very complex, 1 = perfect circle)
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * (area / (perimeter * perimeter))
                    # Low circularity indicates spaghetti (complex shape)
                    if circularity < 0.5:
                        complexity_score += (1 - circularity)
        
        if total_area > 0:
            # Normalize complexity score
            avg_complexity = complexity_score / len(contours) if len(contours) > 0 else 0
            return min(1.0, avg_complexity)
        
        return 0.0
    
    def _detect_temperature_anomaly(self, frame: np.ndarray) -> float:
        """
        Detect temperature-related issues (discoloration, overheating).
        
        Args:
            frame: Current camera frame
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Look for excessive brightness/diffuse reflection (overheating)
        h, s, v = cv2.split(hsv)
        
        # High value (brightness) indicates overheating
        bright_pixels = cv2.countNonZero(
            cv2.inRange(v, 200, 255)
        )
        
        frame_area = frame.shape[0] * frame.shape[1]
        brightness_ratio = bright_pixels / frame_area
        
        # Normalize to confidence score
        confidence = min(1.0, brightness_ratio * 10)
        
        return confidence
    
    def _analyze_frame(self, frame: np.ndarray) -> Tuple[FailureType, float]:
        """
        Analyze a single frame for failures.
        
        Args:
            frame: Camera frame to analyze
            
        Returns:
            Tuple of (detected_failure, confidence_score)
        """
        spaghetti_score = self._detect_spaghetti(frame)
        temp_score = self._detect_temperature_anomaly(frame)
        
        # Return highest confidence failure
        if spaghetti_score > temp_score:
            return FailureType.SPAGHETTI, spaghetti_score
        elif temp_score > 0.3:
            return FailureType.TEMP_ANOMALY, temp_score
        else:
            return FailureType.NONE, 0.0
    
    def detect_failure(self) -> Tuple[FailureType, float]:
        """
        Analyze current camera frame for failures.
        
        Returns:
            Tuple of (detected_failure, confidence_score)
        """
        if not self._connected:
            return FailureType.NONE, 0.0
        
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return FailureType.NONE, 0.0
        
        result, confidence = self._analyze_frame(frame)
        
        # Apply smoothing
        smoothed = self._apply_smoothing(result)
        
        return smoothed, confidence
    
    def is_failure_detected(self) -> bool:
        """
        Check if a failure is currently detected.
        
        Returns:
            True if any failure is detected above threshold
        """
        failure, confidence = self.detect_failure()
        return confidence >= self.threshold and failure != FailureType.NONE
    
    def get_status(self) -> Dict[str, any]:
        """
        Get current detection status.
        
        Returns:
            Dictionary with status information
        """
        failure, confidence = self.detect_failure()
        
        return {
            "failure_type": failure.value,
            "confidence": confidence,
            "is_detected": confidence >= self.threshold,
            "camera_connected": self._connected,
            "last_update": time.time()
        }


class WebcamSimulator:
    """Simulator for testing without physical webcam."""
    
    def __init__(self, failure_type: Optional[FailureType] = None):
        """
        Initialize simulator.
        
        Args:
            failure_type: Simulate specific failure type, or None for normal operation
        """
        self.failure_type = failure_type
        self._frame_count = 0
    
    def generate_frame(self) -> np.ndarray:
        """
        Generate a simulated camera frame.
        
        Returns:
            Simulated frame numpy array
        """
        # Create a synthetic frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :] = [50, 50, 50]  # Gray background
        
        # Simulate 3D printer bed
        frame[200:400, 100:540] = [100, 100, 100]
        
        # Simulate print object
        if self.failure_type == FailureType.SPAGHETTI:
            # Draw tangled filament
            self._draw_spaghetti(frame)
        elif self.failure_type == FailureType.TEMP_ANOMALY:
            # Draw bright overheated area
            cv2.circle(frame, (320, 300), 80, (255, 255, 255), -1)
        
        self._frame_count += 1
        return frame
    
    def _draw_spaghetti(self, frame: np.ndarray) -> None:
        """Draw simulated spaghetti failure."""
        for _ in range(50):
            x = np.random.randint(100, 540)
            y = np.random.randint(200, 400)
            length = np.random.randint(10, 50)
            angle = np.random.uniform(0, 2 * np.pi)
            
            x2 = int(x + length * np.cos(angle))
            y2 = int(y + length * np.sin(angle))
            
            color = np.random.choice([
                [255, 0, 0], [0, 255, 0], [0, 0, 255],
                [255, 255, 0], [255, 0, 255]
            ])
            
            cv2.line(frame, (x, y), (x2, y2), color, 3)
    
    def get_status(self) -> Dict[str, any]:
        """Get simulator status."""
        return {
            "failure_type": self.failure_type.value if self.failure_type else "none",
            "frames_generated": self._frame_count,
            "is_simulated": True
        }
