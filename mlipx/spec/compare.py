import itertools

from deepdiff import DeepDiff

from mlipx.spec.spec import MLIPSpec


def strip_metadata(obj):
    """Recursively remove all 'metadata' keys from nested dicts/lists."""
    if isinstance(obj, dict):
        return {k: strip_metadata(v) for k, v in obj.items() if k != "metadata"}
    elif isinstance(obj, list):
        return [strip_metadata(i) for i in obj]
    else:
        return obj


def compare_specs(specs: dict[str, MLIPSpec]):
    """Compare resolved MLIPSpecs, returning a flat mapping of differences."""
    specs = {k: v.resolve_datasets() for k, v in specs.items()}
    differences = {}

    keys = list(specs.keys())
    if len(keys) < 2:
        raise ValueError("compare_specs requires at least two specs to compare.")

    for i, j in itertools.combinations(range(len(keys)), 2):
        key_a = keys[i]
        key_b = keys[j]

        spec_a = strip_metadata(specs[key_a].model_dump())
        spec_b = strip_metadata(specs[key_b].model_dump())

        diff = DeepDiff(spec_a, spec_b, ignore_order=True)
        if "values_changed" in diff:
            changes = {
                path: {
                    key_a: details["old_value"],
                    key_b: details["new_value"],
                }
                for path, details in diff["values_changed"].items()
            }
            differences[(key_a, key_b)] = changes

    return differences
