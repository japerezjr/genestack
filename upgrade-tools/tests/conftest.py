"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_yaml_data():
    """Sample YAML data for testing."""
    return {
        "charts": {
            "keystone": "2024.1-ubuntu_jammy",
            "nova": "2024.1-ubuntu_jammy",
            "neutron": "2024.2-ubuntu_jammy",
        },
        "metadata": {
            "release": "caracal",
            "version": "2024.1"
        }
    }
