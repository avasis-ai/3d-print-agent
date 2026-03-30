"""CLI interface for 3D-Print-Agent."""

import click
import yaml
import sys
from typing import List, Optional
from pathlib import Path

from .vision_monitor import FailureDetector, FailureType, WebcamSimulator
from .octoprint_client import OctoPrintClient, GCodeAnalyzer


@click.group()
@click.version_option(version="0.1.0", prog_name="3d-print-agent")
def main():
    """3D-Print-Agent: Real-time monitoring and correction for 3D prints."""
    pass


@main.command()
@click.option('--camera', '-c', default=0,
              help='Camera device index')
@click.option('--threshold', '-t', default=0.7,
              type=float,
              help='Detection confidence threshold')
def monitor(camera: int, threshold: float) -> None:
    """Run real-time failure monitoring."""
    try:
        detector = FailureDetector(camera_source=camera, threshold=threshold)
        
        if not detector.connect():
            click.echo("✗ Failed to connect to camera", err=True)
            sys.exit(1)
        
        click.echo(f"✓ Connected to camera {camera}")
        click.echo("Press Ctrl+C to stop monitoring\n")
        
        while True:
            status = detector.get_status()
            
            if status["is_detected"]:
                click.echo(
                    f"⚠️ FAILURE DETECTED: {status['failure_type']} "
                    f"(confidence: {status['confidence']:.2f})"
                )
            else:
                click.echo(
                    f"✓ Monitor OK - Confidence: {status['confidence']:.2f}"
                )
            
            click.echo(f"  Last update: {status['last_update']}")
            click.echo("-" * 50)
            
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        click.echo("\n\nMonitoring stopped.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--octoprint-url', '-u', required=True,
              help='OctoPrint server URL')
@click.option('--api-key', '-k', required=True,
              help='OctoPrint API key')
@click.option('--test-only', is_flag=True,
              help='Only test connection, don\'t run agent')
def octoprint(octoprint_url: str, api_key: str, test_only: bool) -> None:
    """Connect to OctoPrint for printer control."""
    try:
        client = OctoPrintClient(base_url=octoprint_url, api_key=api_key)
        
        if not client.connect():
            click.echo("✗ Failed to connect to OctoPrint", err=True)
            sys.exit(1)
        
        click.echo(f"✓ Connected to {octoprint_url}")
        
        if test_only:
            client.disconnect()
            click.echo("Connection test successful.")
            return
        
        # Get printer status
        status = client.get_printer_status()
        click.echo(f"✓ Printer: {status.get('name', 'Unknown')}")
        click.echo(f"✓ State: {status.get('flags', {})}")
        
        # Get temperatures
        temps = client.get_temperatures()
        for tool in temps.get('temps', []):
            if 'actual' in tool:
                click.echo(
                    f"✓ Bed: {tool.get('bedActual', 'N/A')}°C / "
                    f"{tool.get('bedTarget', 'N/A')}°C"
                )
        
        client.disconnect()
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--config', '-c', required=True,
              type=click.Path(exists=True),
              help='Configuration YAML file')
def analyze(config: str) -> None:
    """Analyze G-Code file for potential issues."""
    try:
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        gcode_content = config_data.get('gcode', '')
        
        if not gcode_content:
            click.echo("✗ No G-Code content in configuration", err=True)
            sys.exit(1)
        
        # Parse G-Code
        analysis = GCodeAnalyzer.parse_gcode(gcode_content)
        
        click.echo(f"✓ Total lines: {analysis['total_lines']}")
        click.echo(f"✓ Total layers: {analysis['total_layers']}")
        
        # Show first few layers
        if analysis['layers']:
            click.echo("\n  Sample layers:")
            for layer in analysis['layers'][:3]:
                click.echo(f"    Layer {layer['layer']}: Z = {layer['z_height']:.2f}mm")
        
    except yaml.YAMLError as e:
        click.echo(f"✗ YAML Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--layers', '-l', default='10:20',
              help='Layer range (start:end)')
@click.option('--height', '-h', default=0.2,
              type=float,
              help='New layer height in mm')
def adjust(layers: str, height: float) -> None:
    """Generate G-Code for layer height adjustment."""
    try:
        start, end = map(int, layers.split(':'))
        
        commands = GCodeAnalyzer.generate_layer_adjustment_gcode(
            start_layer=start,
            end_layer=end,
            layer_height=height
        )
        
        click.echo("# Generated G-Code for layer height adjustment")
        click.echo(f"# Layers: {start} to {end}")
        click.echo(f"# Height: {height}mm\n")
        
        for cmd in commands:
            click.echo(cmd)
            
    except ValueError:
        click.echo("✗ Invalid layer range format. Use start:end", err=True)
        sys.exit(1)


@main.command()
def test() -> None:
    """Run health check on the setup."""
    try:
        # Test simulator
        click.echo("Testing failure detection simulator...")
        
        # Test with normal operation
        normal = WebcamSimulator(failure_type=None)
        status = normal.get_status()
        click.echo(f"✓ Normal operation: {status['failure_type']}")
        
        # Test with spaghetti failure
        spaghetti = WebcamSimulator(failure_type=FailureType.SPAGHETTI)
        frame = spaghetti.generate_frame()
        click.echo(f"✓ Spaghetti simulation: Generated frame {frame.shape}")
        
        # Test with temperature anomaly
        temp = WebcamSimulator(failure_type=FailureType.TEMP_ANOMALY)
        frame = temp.generate_frame()
        click.echo(f"✓ Temperature anomaly: Generated frame {frame.shape}")
        
        click.echo("\n✓ All tests passed!")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
