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

## Integration Testing

Before deploying to production, comprehensive integration testing should be performed in a lab environment.

### Quick Start

```bash
# Set up environment variables (see docs/LAB_ENVIRONMENT_SETUP.md)
source ~/lab-env.sh

# Run interactive testing checklist
./scripts/integration-test-checklist.sh
```

### Documentation

- **[INTEGRATION_TESTING_README.md](INTEGRATION_TESTING_README.md)** - Integration testing overview
- **[docs/INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md)** - Detailed testing guide
- **[docs/LAB_ENVIRONMENT_SETUP.md](docs/LAB_ENVIRONMENT_SETUP.md)** - Lab setup instructions

### Testing Phases

1. **Lab Deployment** - Deploy fresh Caracal environment (20-30 min)
2. **Pre-Upgrade Validation** - Test validation scripts (10-15 min)
3. **Upgrade Execution** - Test complete upgrade (30-60 min)
4. **Post-Upgrade Verification** - Verify functionality (15-20 min)
5. **Rollback Testing** - Test rollback capability (45-60 min)

See [INTEGRATION_TESTING_README.md](INTEGRATION_TESTING_README.md) for complete details.
