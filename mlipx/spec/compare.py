import itertools
from typing import Any

from pydantic import BaseModel

from mlipx.spec.spec import MLIPSpec


def strip_metadata(obj: Any) -> Any:
    """Recursively remove all 'metadata' keys from nested dicts/lists."""
    if isinstance(obj, dict):
        return {k: strip_metadata(v) for k, v in obj.items() if k != "metadata"}
    elif isinstance(obj, list):
        return [strip_metadata(i) for i in obj]
    else:
        return obj


def find_differences(a, b, prefix=""):
    """Recursively compare two nested dicts and return a flat diff."""
    differences = {}
    keys = set(a.keys()) | set(b.keys())
    for key in keys:
        val_a = a.get(key, None)
        val_b = b.get(key, None)
        path = f"{prefix}.{key}" if prefix else key

        if val_a is None and val_b is None:
            continue  # Skip if both sides are None

        if isinstance(val_a, dict) and isinstance(val_b, dict):
            differences.update(find_differences(val_a, val_b, path))
        elif val_a is None and isinstance(val_b, dict):
            differences.update(find_differences({}, val_b, path))
        elif val_b is None and isinstance(val_a, dict):
            differences.update(find_differences(val_a, {}, path))
        elif val_a != val_b:
            differences[path] = {"old": val_a, "new": val_b}

    return differences


def compare_specs(specs: dict[str, MLIPSpec | None]):
    """Compare resolved MLIPSpecs, returning a flat mapping of differences."""

    class EmptyModel(BaseModel):
        """A model to represent an empty spec."""

    resolved_specs = {}
    for k, v in specs.items():
        if v is None:
            resolved_specs[k] = EmptyModel()
        else:
            resolved_specs[k] = v.resolve_datasets()
    differences = {}

    keys = list(resolved_specs.keys())
    if len(keys) < 2:
        raise ValueError("compare_specs requires at least two specs to compare.")

    for key_a, key_b in itertools.combinations(keys, 2):
        spec_a = strip_metadata(resolved_specs[key_a].model_dump())
        spec_b = strip_metadata(resolved_specs[key_b].model_dump())

        raw_diff = find_differences(spec_a, spec_b)
        if raw_diff:
            differences[(key_a, key_b)] = {
                path: {key_a: v["old"], key_b: v["new"]} for path, v in raw_diff.items()
            }

    return differences
