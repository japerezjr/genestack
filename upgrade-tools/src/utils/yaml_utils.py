"""YAML file reading and writing utilities."""

import yaml
from pathlib import Path
from typing import Any, Dict, Union


def read_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read and parse a YAML file.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        Parsed YAML content as a dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file contains invalid YAML
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        try:
            content = yaml.safe_load(f)
            return content if content is not None else {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML file {file_path}: {e}")


def write_yaml_file(file_path: Union[str, Path], data: Dict[str, Any]) -> None:
    """
    Write data to a YAML file.
    
    Args:
        file_path: Path to the YAML file
        data: Data to write (must be serializable to YAML)
        
    Raises:
        yaml.YAMLError: If the data cannot be serialized to YAML
        IOError: If the file cannot be written
    """
    path = Path(file_path)
    
    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to write YAML file {file_path}: {e}")
    except IOError as e:
        raise IOError(f"Failed to write file {file_path}: {e}")
