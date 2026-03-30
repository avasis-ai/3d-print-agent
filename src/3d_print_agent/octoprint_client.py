"""OctoPrint API client for printer communication."""

import httpx
from typing import Dict, List, Optional, Tuple
import json


class OctoPrintClient:
    """Client for interacting with OctoPrint API."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0
    ):
        """
        Initialize OctoPrint client.
        
        Args:
            base_url: OctoPrint server base URL (e.g., 'http://192.168.1.100:8080')
            api_key: OctoPrint API key
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
        self._connected = False
    
    def _create_client(self) -> httpx.Client:
        """Create HTTP client with proper headers."""
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "X-Api-Key": self.api_key
            }
        )
    
    def connect(self) -> bool:
        """Test connection to OctoPrint server."""
        try:
            self._client = self._create_client()
            
            # Test connection
            response = self._client.get("/api/version")
            
            if response.status_code == 200:
                self._connected = True
                return True
            else:
                return False
        except httpx.RequestError:
            return False
    
    def disconnect(self) -> None:
        """Close client connection."""
        if self._client:
            self._client.close()
            self._client = None
        self._connected = False
    
    def get_printer_status(self) -> Dict:
        """
        Get current printer status.
        
        Returns:
            Dictionary with printer status information
        """
        if not self._connected:
            raise RuntimeError("Not connected to OctoPrint")
        
        response = self._client.get("/api/printer")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"Failed to get status: {response.status_code}")
    
    def get_temperatures(self) -> Dict:
        """
        Get current temperatures.
        
        Returns:
            Dictionary with temperature readings
        """
        if not self._connected:
            raise RuntimeError("Not connected to OctoPrint")
        
        response = self._client.get("/api/printer/temps")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"Failed to get temperatures: {response.status_code}")
    
    def get_gcode_status(self) -> Dict:
        """
        Get current G-Code execution status.
        
        Returns:
            Dictionary with G-Code status
        """
        if not self._connected:
            raise RuntimeError("Not connected to OctoPrint")
        
        response = self._client.get("/api/job")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"Failed to get G-Code status: {response.status_code}")
    
    def halt_print(self) -> bool:
        """
        Immediately halt the current print.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            raise RuntimeError("Not connected to OctoPrint")
        
        try:
            response = self._client.post("/api/printer", json={"command": "cancel"})
            return response.status_code == 202
        except httpx.RequestError:
            return False
    
    def resume_print(self) -> bool:
        """
        Resume a paused print.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            raise RuntimeError("Not connected to OctoPrint")
        
        try:
            response = self._client.post("/api/printer", json={"command": "resume"})
            return response.status_code == 202
        except httpx.RequestError:
            return False
    
    def pause_print(self) -> bool:
        """
        Pause the current print.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            raise RuntimeError("Not connected to OctoPrint")
        
        try:
            response = self._client.post("/api/printer", json={"command": "pause"})
            return response.status_code == 202
        except httpx.RequestError:
            return False
    
    def send_gcode(self, gcode_commands: List[str]) -> List[Dict]:
        """
        Send G-Code commands to the printer.
        
        Args:
            gcode_commands: List of G-Code commands to execute
            
        Returns:
            List of command results
        """
        if not self._connected:
            raise RuntimeError("Not connected to OctoPrint")
        
        try:
            results = []
            for command in gcode_commands:
                response = self._client.post(
                    "/api/printer/gcode",
                    json={"command": command}
                )
                
                if response.status_code == 200:
                    results.append({
                        "command": command,
                        "success": True,
                        "status_code": response.status_code
                    })
                else:
                    results.append({
                        "command": command,
                        "success": False,
                        "status_code": response.status_code
                    })
            
            return results
        except httpx.RequestError as e:
            return [{
                "command": str(gcode_commands),
                "success": False,
                "error": str(e)
            }]
    
    def adjust_layer_height(
        self,
        current_layer: int,
        new_height: float,
        affected_layers: int = 5
    ) -> bool:
        """
        Adjust layer height for affected layers.
        
        Args:
            current_layer: Current layer being printed
            new_height: Desired layer height in mm
            affected_layers: Number of layers to adjust
            
        Returns:
            True if adjustment successful
        """
        gcode_commands = [
            f"M204 S{new_height}  # Set acceleration",
            f"G92 Z{current_layer * new_height:.4f}  # Set current Z position"
        ]
        
        results = self.send_gcode(gcode_commands)
        
        return all(r.get("success", False) for r in results)
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected
    
    def test_connection(self) -> bool:
        """Test connection and return status."""
        return self.connect()


class GCodeAnalyzer:
    """Analyzer for G-Code files."""
    
    @staticmethod
    def parse_gcode(gcode_string: str) -> Dict:
        """
        Parse G-Code string into structured data.
        
        Args:
            gcode_string: G-Code program string
            
        Returns:
            Dictionary with parsed G-Code information
        """
        lines = gcode_string.strip().split('\n')
        layers: List[Dict] = []
        current_layer = 0
        current_z = 0.0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            # Parse Z-height changes
            if 'Z' in line:
                try:
                    z_value = float(line.split('Z')[1].split()[0])
                    if z_value != current_z:
                        current_layer += 1
                        current_z = z_value
                        layers.append({
                            "layer": current_layer,
                            "z_height": z_value
                        })
                except (ValueError, IndexError):
                    pass
        
        return {
            "total_layers": len(layers),
            "layers": layers,
            "total_lines": len(lines)
        }
    
    @staticmethod
    def generate_layer_adjustment_gcode(
        start_layer: int,
        end_layer: int,
        layer_height: float
    ) -> List[str]:
        """
        Generate G-Code commands for layer height adjustment.
        
        Args:
            start_layer: Starting layer number
            end_layer: Ending layer number
            layer_height: New layer height in mm
            
        Returns:
            List of G-Code commands
        """
        commands = [
            "# Layer height adjustment",
            f"# Layer {start_layer} to {end_layer}",
            f"# New height: {layer_height}mm",
            "M82  # Extruder absolute positioning",
            "M204 S1500  # Increase acceleration"
        ]
        
        # Add layer-specific commands
        for layer in range(start_layer, min(end_layer, start_layer + 5)):
            z_position = layer * layer_height
            commands.extend([
                f"; Layer {layer}",
                f"G92 Z{z_position:.4f}",
                "M204 S1000"
            ])
        
        return commands
