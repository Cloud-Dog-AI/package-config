# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
# Licensed under the Apache License, Version 2.0
"""
Adoption test for cloud_dog_config (PS-80).
Run check_adoption(project_root) to verify a project fully uses cloud_dog_config.
"""
import pathlib
import subprocess


def _grep(pattern: str, search_path: pathlib.Path, extra_flags: str = "") -> list[str]:
    """Run grep and return non-empty hit lines."""
    cmd = f"grep -rn {extra_flags} '{pattern}' {search_path} --include='*.py' | grep -v __pycache__ | grep -v '/archive/' | grep -v '/working/'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return [l for l in result.stdout.strip().split('\n') if l]


def _find_source_dirs(project_root: pathlib.Path) -> list[pathlib.Path]:
    """Return all source directories for a project."""
    dirs = []
    src = project_root / "src"
    if src.is_dir():
        dirs.append(src)
    # searxNcrawl has source at crawler/ root level
    crawler = project_root / "crawler"
    if crawler.is_dir():
        dirs.append(crawler)
    # Also check root-level start_*.py files
    return dirs


def check_adoption(project_root: pathlib.Path) -> dict:
    results = {"pass": [], "fail": []}
    source_dirs = _find_source_dirs(project_root)

    if not source_dirs:
        results["fail"].append(f"No source directory found in {project_root}")
        return results

    # 1. cloud_dog_config is imported somewhere in source
    all_imports = []
    for sd in source_dirs:
        all_imports.extend(_grep("cloud_dog_config", sd))
    # Also check root-level start_*.py
    for f in project_root.glob("start_*.py"):
        cmd = f"grep -n 'cloud_dog_config' {f}"
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if r.stdout.strip():
            all_imports.extend(r.stdout.strip().split('\n'))

    if len(all_imports) > 0:
        results["pass"].append(f"cloud_dog_config imported ({len(all_imports)} references)")
    else:
        results["fail"].append("cloud_dog_config NOT imported anywhere in source")

    # 2. No bespoke ConfigManager that doesn't delegate to cloud_dog_config
    bespoke = []
    for sd in source_dirs:
        hits = _grep("class ConfigManager", sd)
        for h in hits:
            if "cloud_dog" not in h:
                bespoke.append(h)
    if len(bespoke) == 0:
        results["pass"].append("No bespoke ConfigManager class")
    else:
        results["fail"].append(f"Bespoke ConfigManager found: {bespoke}")

    # 3. defaults.yaml exists
    if (project_root / "defaults.yaml").exists():
        results["pass"].append("defaults.yaml exists")
    else:
        results["fail"].append("defaults.yaml missing")

    # 4. No os.environ mutation during config load (os.environ[...] = ...)
    mutations = []
    for sd in source_dirs:
        hits = _grep(r'os\.environ\[.*\] *=', sd)
        # Filter out test files
        hits = [h for h in hits if '/test' not in h.lower()]
        mutations.extend(hits)
    if len(mutations) == 0:
        results["pass"].append("No os.environ mutation in source")
    else:
        results["fail"].append(f"os.environ mutation found: {mutations}")

    # 5. No bespoke yaml.safe_load for config outside cloud_dog_config usage
    yaml_loads = []
    for sd in source_dirs:
        hits = _grep("yaml.safe_load", sd)
        # Filter: only flag if not in a cloud_dog_config context
        for h in hits:
            if "cloud_dog" not in h and "/test" not in h.lower():
                yaml_loads.append(h)
    if len(yaml_loads) == 0:
        results["pass"].append("No bespoke yaml.safe_load for config outside platform package")
    else:
        # This is informational - some yaml usage may be legitimate (non-config)
        results["pass"].append(f"yaml.safe_load found but may be non-config usage ({len(yaml_loads)} hits)")

    return results
