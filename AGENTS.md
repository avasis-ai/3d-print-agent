# AGENTS.md - 3D-Print-Agent Project Context

This folder is home. Treat it that way.

## Project: 3D-Print-Agent (#91)

### Identity
- **Name**: 3D-Print-Agent
- **License**: GPL-3.0
- **Org**: avasis-ai
- **PyPI**: 3d-print-agent
- **Version**: 0.1.0
- **Tagline**: The agent that monitors and corrects your 3D prints in real-time

### What It Does
Utilizing vision models and SKILL.md, this agent monitors a 3D printer webcam. If it detects a spaghetti failure or temperature anomaly, it autonomously halts the print, adjusts the G-Code, and alerts the user, saving material.

### Inspired By
- OctoPrint
- G-Code
- Hardware + Manufacturing
- Computer Vision
- Real-time monitoring systems

### Core Components

#### `/vision-monitor/`
- Vision-based failure detection
- Spaghetti detection algorithms
- Temperature anomaly detection
- Webcam simulator for testing

#### `/octoprint-plugin/`
- OctoPrint API integration
- Printer control commands
- G-Code management

#### `/agent-core/`
- CLI interface
- Configuration management
- Alert/notification system

### Technical Architecture

**Key Dependencies:**
- `opencv-python>=4.8` - Computer vision (Trust score: 7.3-10)
- `pyyaml>=6.0` - Configuration parsing (Trust score: 7.4)
- `httpx>=0.25` - HTTP client (Trust score: 6.5-10)

**Core Modules:**
1. `vision_monitor.py` - Failure detection using computer vision
2. `octoprint_client.py` - OctoPrint API integration and G-Code management
3. `cli.py` - Command-line interface

### AI Coding Agent Guidelines

#### When Contributing:

1. **Understand the problem**: 3D printing failures are expensive and frustrating. This agent prevents waste by catching issues early.

2. **Use Context7**: Check trust scores for new libraries before adding dependencies.

3. **Respect the domain**: 3D printing has specific failure modes (spaghetti, warping, detachment, temperature issues).

4. **Type safety**: Always use type hints and docstrings.

5. **Testing**: Use WebcamSimulator for testing without physical hardware.

#### What to Remember:

- **Spaghetti detection**: Complex filament patterns indicate extrusion errors
- **Temperature anomalies**: Overheating shows as excessive brightness in frames
- **Real-time requirement**: Detection must be fast (<1 second per frame)
- **Smoothing**: Apply temporal smoothing to avoid false positives
- **OctoPrint control**: Can halt, pause, resume prints programmatically

#### Common Patterns:

**Monitor in real-time:**
```python
from 3d_print_agent.vision_monitor import FailureDetector

detector = FailureDetector(camera_source=0)
detector.connect()

while True:
    failure, confidence = detector.detect_failure()
    
    if failure == FailureType.SPAGHETTI and confidence > 0.7:
        client.halt_print()
```

**OctoPrint integration:**
```python
from 3d_print_agent.octoprint_client import OctoPrintClient

client = OctoPrintClient(
    base_url='http://printer:8080',
    api_key='your_api_key'
)
client.connect()
status = client.get_printer_status()
```

**G-Code analysis:**
```python
from 3d_print_agent.octoprint_client import GCodeAnalyzer

analysis = GCodeAnalyzer.parse_gcode(gcode_string)
print(f"Layers: {analysis['total_layers']}")
```

### Project Status

- ✅ Initial implementation complete
- ✅ Vision monitoring with real detection
- ✅ OctoPrint API integration
- ✅ CLI interface
- ✅ Comprehensive test suite
- ✅ Webcam simulator for testing
- ⚠️ SKILL.md integration pending
- ⚠️ Production failure patterns dataset needed

### How to Work with This Project

1. **Read `SOUL.md`** - Understand who you are
2. **Read `USER.md`** - Know who you're helping
3. **Check `memory/YYYY-MM-DD.md`** - Recent context
4. **Read `MEMORY.md`** - Long-term decisions (main session only)
5. **Execute**: Code → Test → Commit

### Red Lines

- **No stubs or TODOs**: Every function must have real implementation
- **Type hints required**: All function signatures must include types
- **Docstrings mandatory**: Explain what, why, and how
- **Test coverage**: New features need tests
- **Real-time performance**: Vision processing must be fast

### Development Workflow

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Format code
black src/ tests/
isort src/ tests/

# Check syntax
python -m py_compile src/3d_print_agent/*.py

# Test CLI
3d-print-agent test

# Commit
git add -A && git commit -m "feat: add failure detection"
```

### Key Files to Understand

- `src/3d_print_agent/vision_monitor.py` - Computer vision and failure detection
- `src/3d_print_agent/octoprint_client.py` - Printer API and G-Code management
- `src/3d_print_agent/cli.py` - Command-line interface
- `tests/test_vision_monitor.py` - Vision tests with simulator
- `tests/test_octoprint_client.py` - API client tests

### Security Considerations

- All processing is local - no external API calls
- Trust model: Personal assistant (one trusted operator boundary)
- Dependencies verified via Context7
- No sensitive data transmitted

### Next Steps

1. Build proprietary failure dataset (millions of labeled images)
2. Train better failure detection models
3. Add more failure types (detachment, warping, extrusion errors)
4. Create SKILL.md integration layer
5. Add notification system (email, push, SMS)
6. Build mobile app for real-time alerts

### Unique Defensible Moat

The **proprietary computer vision dataset of millions of specific 3D printing failure modes, materials, and lighting conditions** makes the detection algorithm highly robust. This is the key competitive advantage - the more data we have, the better the detection becomes.

---

**This file should evolve as you learn more about the project.**
