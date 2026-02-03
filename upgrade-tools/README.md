# OpenStack Caracal to Epoxy Upgrade Tools

This directory contains tooling for upgrading Genestack OpenStack deployments from Caracal (2024.1/2024.2) to Epoxy (2025.1).

## Structure

- `src/` - Python source code
  - `config/` - Configuration management
  - `version/` - Chart version management
  - `validation/` - Configuration validation
  - `breaking_changes/` - Breaking change detection
  - `health/` - Service health monitoring
  - `executor/` - Helm execution
  - `rollback/` - Rollback management
  - `logging/` - Logging and reporting
  - `utils/` - Shared utilities
- `scripts/` - Bash wrapper scripts
- `tests/` - Test suite
- `config/` - Configuration files

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/
```

## Usage

See individual component documentation for usage details.
