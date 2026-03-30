# README.md - 3D-Print-Agent

## Real-Time Monitoring and Correction for 3D Printing

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/3d-print-agent.svg)](https://pypi.org/project/3d-print-agent/)

**3D-Print-Agent** is an intelligent monitoring system that uses computer vision to detect and correct 3D printing failures in real-time, saving material and preventing expensive print failures.

## 🎯 What It Does

Using advanced computer vision and integration with OctoPrint, 3D-Print-Agent:

- **Monitors** your 3D printer in real-time via webcam
- **Detects** failures: spaghetti, temperature anomalies, detachment, warping
- **Corrects** issues automatically or alerts you to intervene
- **Saves material** by catching problems before they become disasters
- **Saves expensive prints** by halting when failure is imminent

### Example Use Case

```python
# Monitor your print in real-time
from 3d_print_agent.vision_monitor import FailureDetector, FailureType

detector = FailureDetector(camera_source=0, threshold=0.7)
detector.connect()

while True:
    failure, confidence = detector.detect_failure()
    
    if failure == FailureType.SPAGHETTI and confidence > 0.8:
        print("Spaghetti detected! Halting print...")
        halt_print()
```

## 🚀 Features

- **Computer Vision Failure Detection**: Real-time analysis of camera feed
- **OctoPrint Integration**: Full printer control and G-Code management
- **Multiple Failure Types**: Detect spaghetti, temperature issues, detachment
- **G-Code Analysis**: Parse and analyze G-Code files for optimization
- **Simulator**: Test without physical hardware using webcam simulator
- **CLI Tools**: Command-line interface for all operations

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- OpenCV 4.8+ (for computer vision)
- OctoPrint (optional, for printer control)
- USB webcam (for monitoring)

### Install from PyPI

```bash
pip install 3d-print-agent
```

### Install from Source

```bash
git clone https://github.com/avasis-ai/3d-print-agent.git
cd 3d-print-agent
pip install -e .
```

### Development Setup

```bash
pip install -e ".[dev]"
pip install pytest pytest-mock black isort
```

## 🔧 Usage

### Command-Line Interface

```bash
# Check version
3d-print-agent --version

# Run health check
3d-print-agent test

# Real-time monitoring
3d-print-agent monitor --camera 0 --threshold 0.7

# Connect to OctoPrint
3d-print-agent octoprint --octoprint-url http://192.168.1.100:8080 --api-key YOUR_KEY

# Analyze G-Code file
3d-print-agent analyze --config analysis.yaml

# Generate layer adjustment G-Code
3d-print-agent adjust --layers 10:20 --height 0.25
```

### Programmatic Usage

```python
from 3d_print_agent.vision_monitor import FailureDetector, FailureType, WebcamSimulator
from 3d_print_agent.octoprint_client import OctoPrintClient, GCodeAnalyzer

# === Real-time Monitoring ===
detector = FailureDetector(camera_source=0, threshold=0.7)

if not detector.connect():
    print("Failed to connect to camera")
    exit(1)

while True:
    failure, confidence = detector.detect_failure()
    
    if failure != FailureType.NONE and confidence > 0.7:
        print(f"FAILURE: {failure.value} (confidence: {confidence:.2f})")
        # Could trigger automatic response:
        # client.halt_print()
    
    import time
    time.sleep(1)

# === OctoPrint Integration ===
client = OctoPrintClient(
    base_url='http://192.168.1.100:8080',
    api_key='your_api_key_here'
)

if client.connect():
    # Get printer status
    status = client.get_printer_status()
    print(f"Printer: {status.get('name')}")
    
    # Get temperatures
    temps = client.get_temperatures()
    print(f"Nozzle: {temps['temps'][0]['actual']}°C")
    
    # Halt print if needed
    if should_stop:
        client.halt_print()
    
    client.disconnect()

# === G-Code Analysis ===
gcode = """
M104 S200
G28
G1 Z0.2 F3000
G1 X10 Y10 E5
...
"""

analysis = GCodeAnalyzer.parse_gcode(gcode)
print(f"Total layers: {analysis['total_layers']}")

# Generate adjustment G-Code
commands = GCodeAnalyzer.generate_layer_adjustment_gcode(
    start_layer=10,
    end_layer=20,
    layer_height=0.2
)
```

### Using the Simulator

```python
from 3d_print_agent.vision_monitor import WebcamSimulator, FailureType

# Simulate normal operation
normal = WebcamSimulator(failure_type=None)
frame = normal.generate_frame()

# Simulate spaghetti failure
spaghetti = WebcamSimulator(failure_type=FailureType.SPAGHETTI)
frame = spaghetti.generate_frame()

# Get simulator status
status = normal.get_status()
print(f"Mode: {status['failure_type']}")
```

## 📚 API Reference

### FailureDetector

Real-time failure detection from camera feed.

#### `__init__(camera_source, threshold, smoothing_window)`

Initialize detector.

**Parameters:**
- `camera_source` (int): Camera device index (default: 0)
- `threshold` (float): Detection threshold (default: 0.7)
- `smoothing_window` (int): Smoothing frames (default: 5)

#### `connect()` → bool

Connect to camera.

#### `detect_failure()` → Tuple[FailureType, float]

Detect current failure.

**Returns:** Tuple of (failure_type, confidence_score)

#### `get_status()` → Dict

Get current detection status.

### FailureDetector

### FailureDetector

## 🧪 Testing

Run tests with pytest:

```bash
python -m pytest tests/ -v
```

Test the CLI:

```bash
3d-print-agent test
```

## 📁 Project Structure

```
3d-print-agent/
├── README.md
├── pyproject.toml
├── LICENSE
├── src/
│   └── 3d_print_agent/
│       ├── __init__.py
│       ├── vision_monitor.py
│       ├── octoprint_client.py
│       └── cli.py
├── tests/
│   ├── test_vision_monitor.py
│   ├── test_octoprint_client.py
│   └── test_cli.py
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── bug_report.md
├── vision-monitor/
└── octoprint-plugin/
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `python -m pytest tests/ -v`
5. **Submit a pull request**

### Development Setup

```bash
git clone https://github.com/avasis-ai/3d-print-agent.git
cd 3d-print-agent
pip install -e ".[dev]"
pre-commit install
```

## 📝 License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0). See [LICENSE](LICENSE) for details.

## 🎯 Vision

3D-Print-Agent democratizes 3D printing reliability by:

- **Reducing waste**: Catch failures before they become spaghetti
- **Saving material**: Stop prints before all filament is wasted
- **Educational**: Learn what failure modes look like
- **Community-driven**: Build on the massive Open Source 3D printing ecosystem

## 🌟 Impact

This tool solves the most painful problem in 3D printing: **wasted prints**. Whether it's:

- **Spaghetti failures**: Over-extrusion and tangled filament
- **Temperature anomalies**: Overheating or poor layer adhesion
- **Detachment**: Print separating from build plate
- **Warping**: Corners lifting off the bed

The computer vision system learns to recognize these patterns and intervenes before the damage is done.

## 🛡️ Security & Trust

- **Local processing**: All vision analysis happens locally
- **No external calls**: No data leaves your machine
- **Trusted dependencies**: OpenCV (7.3-10), httpx (6.5-10), PyYAML (7.4) - [Context7 verified](https://context7.com)
- **GPL-3.0**: Open source, community-driven

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/avasis-ai/3d-print-agent/wiki)
- **Issues**: [GitHub Issues](https://github.com/avasis-ai/3d-print-agent/issues)
- **Community**: [3D Printing Discord](https://discord.gg/3dprinting)

## 🙏 Acknowledgments

- **OctoPrint team** for the excellent API
- **OpenCV** for the computer vision libraries
- **3D printing community** for shared knowledge
- **Blender Foundation** (inspiration from related projects)

---

**Made with ❤️ by [Avasis AI](https://avasis.ai)**

*Prevent failures before they happen. Monitor, detect, correct.*
