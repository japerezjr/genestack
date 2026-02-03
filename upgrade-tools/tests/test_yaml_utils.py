"""Unit tests for YAML utilities."""

import pytest
import yaml
from pathlib import Path
from src.utils.yaml_utils import read_yaml_file, write_yaml_file


def test_read_yaml_file_success(temp_dir, sample_yaml_data):
    """Test reading a valid YAML file."""
    yaml_file = temp_dir / "test.yaml"
    
    # Write test data
    with open(yaml_file, 'w') as f:
        yaml.safe_dump(sample_yaml_data, f)
    
    # Read and verify
    result = read_yaml_file(yaml_file)
    assert result == sample_yaml_data


def test_read_yaml_file_not_found():
    """Test reading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_yaml_file("nonexistent.yaml")


def test_read_yaml_file_invalid_yaml(temp_dir):
    """Test reading invalid YAML raises YAMLError."""
    yaml_file = temp_dir / "invalid.yaml"
    
    # Write invalid YAML
    with open(yaml_file, 'w') as f:
        f.write("invalid: yaml: content:\n  - broken")
    
    with pytest.raises(yaml.YAMLError):
        read_yaml_file(yaml_file)


def test_read_yaml_file_empty(temp_dir):
    """Test reading an empty YAML file returns empty dict."""
    yaml_file = temp_dir / "empty.yaml"
    yaml_file.touch()
    
    result = read_yaml_file(yaml_file)
    assert result == {}


def test_write_yaml_file_success(temp_dir, sample_yaml_data):
    """Test writing data to a YAML file."""
    yaml_file = temp_dir / "output.yaml"
    
    write_yaml_file(yaml_file, sample_yaml_data)
    
    # Verify file was created and contains correct data
    assert yaml_file.exists()
    with open(yaml_file, 'r') as f:
        result = yaml.safe_load(f)
    assert result == sample_yaml_data


def test_write_yaml_file_creates_directories(temp_dir, sample_yaml_data):
    """Test that write_yaml_file creates parent directories."""
    yaml_file = temp_dir / "subdir" / "nested" / "output.yaml"
    
    write_yaml_file(yaml_file, sample_yaml_data)
    
    assert yaml_file.exists()
    with open(yaml_file, 'r') as f:
        result = yaml.safe_load(f)
    assert result == sample_yaml_data


def test_write_yaml_file_overwrites_existing(temp_dir):
    """Test that write_yaml_file overwrites existing files."""
    yaml_file = temp_dir / "output.yaml"
    
    # Write initial data
    initial_data = {"key": "value1"}
    write_yaml_file(yaml_file, initial_data)
    
    # Overwrite with new data
    new_data = {"key": "value2"}
    write_yaml_file(yaml_file, new_data)
    
    # Verify new data
    with open(yaml_file, 'r') as f:
        result = yaml.safe_load(f)
    assert result == new_data


def test_yaml_round_trip(temp_dir, sample_yaml_data):
    """Test that data survives a write-read round trip."""
    yaml_file = temp_dir / "roundtrip.yaml"
    
    # Write then read
    write_yaml_file(yaml_file, sample_yaml_data)
    result = read_yaml_file(yaml_file)
    
    assert result == sample_yaml_data
