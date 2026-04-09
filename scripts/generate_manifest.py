#!/usr/bin/env python3
"""
Generate manifest.json for OCR Detection application

This script is used in CI/CD to create manifest.json containing:
- File inventory with SHA256 hashes
- Package organization (core vs deps)
- Download sizes for each package

Usage:
    python scripts/generate_manifest.py dist/DRB-OCR-AI/ 1.2.0
"""

import json
import hashlib
import sys
import os
from pathlib import Path
from typing import Dict, Tuple


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def categorize_file(file_path: Path, rel_path: str) -> str:
    """
    Categorize file as 'core' or 'deps'
    - core: app code, UI, main exe
    - deps: python dependencies (_internal/)
    """
    if "_internal" in rel_path:
        return "deps"
    return "core"


def generate_manifest(app_dir: Path, version: str) -> Dict:
    """
    Generate manifest for the application directory

    Args:
        app_dir: Path to dist/DRB-OCR-AI/ directory
        version: Application version (e.g., "1.2.0")

    Returns:
        Dictionary containing manifest structure
    """
    if not app_dir.exists():
        print(f"Error: Directory not found: {app_dir}")
        sys.exit(1)

    manifest = {
        "version": version,
        "generated_date": "",
        "files": {},
        "packages": {
            "core": {"size": 0, "asset": f"DRB-OCR-AI-v{version}-core.zip"},
            "full": {"size": 0, "asset": f"DRB-OCR-AI-v{version}-full.zip"}
        }
    }

    from datetime import datetime
    manifest["generated_date"] = datetime.now().isoformat()

    # Walk through all files
    core_size = 0
    full_size = 0

    print(f"Scanning directory: {app_dir}")
    print(f"Generating manifest for version: {version}")
    print()

    for file_path in app_dir.rglob("*"):
        if not file_path.is_file():
            continue

        # Calculate relative path
        rel_path = str(file_path.relative_to(app_dir))
        rel_path = rel_path.replace("\\", "/")  # Normalize to forward slashes

        # Calculate file size
        file_size = file_path.stat().st_size

        # Calculate hash
        try:
            file_hash = calculate_sha256(file_path)
        except Exception as e:
            print(f"Warning: Could not hash {rel_path}: {e}")
            continue

        # Categorize file
        category = categorize_file(file_path, rel_path)

        # Add to manifest
        manifest["files"][rel_path] = {
            "hash": file_hash,
            "size": file_size,
            "package": category
        }

        # Update size counters
        full_size += file_size
        if category == "core":
            core_size += file_size

    # Update package sizes
    manifest["packages"]["core"]["size"] = core_size
    manifest["packages"]["full"]["size"] = full_size

    return manifest


def create_split_zips(app_dir: Path, version: str, output_dir: Path = None):
    """
    Create core.zip and full.zip for the application

    Args:
        app_dir: Path to dist/DRB-OCR-AI/ directory
        version: Application version
        output_dir: Where to save the ZIP files (defaults to app_dir.parent)
    """
    if output_dir is None:
        output_dir = app_dir.parent

    import zipfile
    import os

    print(f"Creating ZIP packages...")
    print()

    # Create core.zip (app code only)
    core_zip_path = output_dir / f"DRB-OCR-AI-v{version}-core.zip"
    print(f"Creating {core_zip_path.name}...")

    try:
        with zipfile.ZipFile(core_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in app_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(app_dir)
                    # Skip _internal directory for core zip
                    if "_internal" not in rel_path.parts:
                        zf.write(file_path, arcname=rel_path)

        core_size_mb = core_zip_path.stat().st_size / (1024 * 1024)
        print(f"[OK] Created: {core_zip_path} ({core_size_mb:.1f} MB)")
    except Exception as e:
        print(f"✗ Error creating core.zip: {e}")
        return False

    # Create full.zip (everything)
    full_zip_path = output_dir / f"DRB-OCR-AI-v{version}-full.zip"
    print(f"Creating {full_zip_path.name}...")

    try:
        with zipfile.ZipFile(full_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in app_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(app_dir)
                    arc_name = Path("DRB-OCR-AI") / rel_path
                    zf.write(file_path, arcname=arc_name)

        full_size_mb = full_zip_path.stat().st_size / (1024 * 1024)
        print(f"[OK] Created: {full_zip_path} ({full_size_mb:.1f} MB)")
    except Exception as e:
        print(f"✗ Error creating full.zip: {e}")
        return False

    print()
    return True


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python generate_manifest.py <app_dir> [version]")
        print("Example: python generate_manifest.py dist/DRB-OCR-AI/ 1.2.0")
        sys.exit(1)

    app_dir = Path(sys.argv[1])
    version = sys.argv[2] if len(sys.argv) > 2 else "1.1.0"

    # Generate manifest
    manifest = generate_manifest(app_dir, version)

    # Save manifest INSIDE app directory (for the installed app to use)
    manifest_path = app_dir / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Manifest saved: {manifest_path}")

    # ALSO save versioned manifest in PARENT directory (for CI/CD release upload)
    versioned_manifest_path = app_dir.parent / f"manifest-v{version}.json"
    with open(versioned_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Versioned manifest saved: {versioned_manifest_path}")

    print()
    print(f"Summary:")
    print(f"  Version: {version}")
    print(f"  Core package: {manifest['packages']['core']['size'] / (1024*1024):.1f} MB")
    print(f"  Full package: {manifest['packages']['full']['size'] / (1024*1024):.1f} MB")
    print(f"  Total files: {len(manifest['files'])}")
    print()

    # Create ZIP files
    print("=" * 60)
    create_split_zips(app_dir, version, app_dir.parent)

    # Verify all output files exist
    print("=" * 60)
    print("Verifying output files:")
    output_dir = app_dir.parent
    expected_files = [
        manifest_path,
        versioned_manifest_path,
        output_dir / f"DRB-OCR-AI-v{version}-core.zip",
        output_dir / f"DRB-OCR-AI-v{version}-full.zip",
    ]
    all_ok = True
    for f in expected_files:
        if f.exists():
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  [OK] {f.name} ({size_mb:.1f} MB)")
        else:
            print(f"  [FAIL] MISSING: {f}")
            all_ok = False

    if all_ok:
        print("\n[OK] All files generated successfully!")
    else:
        print("\n[FAIL] Some files are missing!")
        sys.exit(1)


if __name__ == "__main__":
    main()
