# Quick Start Guide

## Initial Setup

1. **Create and activate virtual environment:**
   ```bash
   cd upgrade-tools
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

2. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

3. **Install test dependencies:**
   ```bash
   pip install pytest pytest-cov hypothesis
   ```

4. **Run tests to verify setup:**
   ```bash
   pytest tests/ -v
   ```

## Project Structure

```
upgrade-tools/
├── src/                          # Source code
│   ├── config/                   # Configuration schemas
│   │   └── schema.py            # Pydantic models
│   ├── utils/                    # Utilities
│   │   └── yaml_utils.py        # YAML read/write
│   ├── version/                  # Version management (TBD)
│   ├── validation/               # Config validation (TBD)
│   ├── breaking_changes/         # Breaking change detection (TBD)
│   ├── health/                   # Health monitoring (TBD)
│   ├── executor/                 # Helm execution (TBD)
│   ├── rollback/                 # Rollback management (TBD)
│   └── logging/                  # Logging and reporting (TBD)
├── tests/                        # Test suite
│   ├── conftest.py              # Pytest fixtures
│   └── test_yaml_utils.py       # YAML utility tests
├── scripts/                      # Bash wrapper scripts (TBD)
├── config/                       # Configuration files
│   └── upgrade-config.yaml      # Sample upgrade config
└── requirements.txt              # Python dependencies
```

## Configuration

Edit `config/upgrade-config.yaml` to customize the upgrade settings:

- Source and target releases
- File paths
- Service categories
- Dependencies
- Breaking changes
- Deprecated options

## Development Workflow

1. **Make changes to source code**
2. **Write tests for new functionality**
3. **Run tests:**
   ```bash
   pytest tests/ -v
   ```
4. **Run with coverage:**
   ```bash
   pytest tests/ --cov=src --cov-report=html
   ```

## Next Steps

The following components need to be implemented (see tasks.md):

- Task 2: Chart Version Manager
- Task 3: Configuration Validator
- Task 5: Breaking Change Detector
- Task 6: Pre-Upgrade Validation
- Task 8: Upgrade Execution Logic
- Task 9: Rollback Manager
- Task 10: Logging and Reporting
- Task 12: Main orchestration script
- Task 13: Bash wrapper scripts

Each task builds on the foundation established here.
