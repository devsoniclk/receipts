"""Task spec parser — reads YAML task specifications."""

from pathlib import Path
from typing import Any

import yaml


def parse_spec(spec_path: str) -> dict[str, Any]:
    """Parse a YAML task spec file.

    Args:
        spec_path: Path to the YAML file.

    Returns:
        Parsed spec dict with keys: goal, probes, anti_gaming.

    Raises:
        FileNotFoundError: If spec file doesn't exist.
        ValueError: If spec is malformed.
    """
    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Task spec not found: {spec_path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Task spec must be a YAML mapping")

    if "goal" not in data:
        raise ValueError("Task spec must have a 'goal' field")

    if "probes" not in data or not isinstance(data["probes"], list):
        raise ValueError("Task spec must have a 'probes' list")

    # Normalize probe definitions: each list item is a single-key dict
    normalized_probes = []
    for probe_def in data["probes"]:
        if not isinstance(probe_def, dict) or len(probe_def) != 1:
            raise ValueError(
                f"Each probe must be a single-key mapping, got: {probe_def}"
            )
        probe_type = next(iter(probe_def))
        probe_config = probe_def[probe_type]
        if not isinstance(probe_config, dict):
            probe_config = {}
        normalized_probes.append({"type": probe_type, **probe_config})

    data["probes"] = normalized_probes

    if "anti_gaming" not in data:
        data["anti_gaming"] = {}

    return data
