import os
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path

# Configuration
PROJECT_NAME = "DM_Toolkit"
# Directories to exclude from the final package
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".claude", "archive", "dist", "design", "scripts"}
# Files to exclude from the final package root
EXCLUDE_FILES = {".env", ".DS_Store", ".gitignore", ".geminiignore", "README.md"}

def get_version():
    """Extract version from server.py"""
    try:
        with open("server.py", "r") as f:
            for line in f:
                if line.strip().startswith('VERSION ='):
                    return line.split('=')[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "1.0.0"

def package():
    # We are running from scripts/package.py, so project root is one level up
    root_dir = Path(__file__).parent.parent.resolve()
    os.chdir(root_dir)
    
    version = get_version()
    dist_dir = root_dir / "dist"
    package_name = f"{PROJECT_NAME}_v{version}"
    build_dir = dist_dir / package_name
    zip_path = dist_dir / f"{package_name}.zip"

    print(f"Packaging {PROJECT_NAME} v{version}...")

    # 1. Clean/Create dist directory
    if dist_dir.exists():
        print(f"  Cleaning existing dist directory...")
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    build_dir.mkdir()

    # 2. Copy files
    for item in root_dir.iterdir():
        if item.name in EXCLUDE_DIRS:
            continue
        if item.name in EXCLUDE_FILES:
            continue
        if item.name.endswith(".zip"):
            continue

        if item.is_dir():
            print(f"  Copying directory: {item.name}")
            shutil.copytree(item, build_dir / item.name, ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '.DS_Store'))
        else:
            print(f"  Copying file: {item.name}")
            shutil.copy2(item, build_dir / item.name)

    # 3. Create macOS App Wrapper (if on macOS)
    if sys.platform == 'darwin':
        print("  Building macOS App Wrapper...")
        # Path to build script inside the build directory
        build_script = build_dir / "tools" / "build_macos_app.sh"
        if build_script.exists():
            try:
                # Run the build script in the build directory context
                subprocess.run(["bash", "tools/build_macos_app.sh"], cwd=build_dir, check=True)
                # After building, we can remove the tools/build_macos_app.sh from the final package if we want,
                # but it's small so keeping it is fine.
            except Exception as e:
                print(f"  Warning: Could not build macOS app wrapper: {e}")
        else:
            print(f"  Warning: build_macos_app.sh not found in {build_dir}/tools/")

    # 4. Create ZIP
    print(f"  Creating ZIP: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # We want the files in the zip to be under a top-level folder named after the package
        for file_path in build_dir.rglob('*'):
            if file_path.is_file():
                # arcname should include the package_name as the top-level directory
                arcname = Path(package_name) / file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)

    print(f"\nSuccess! Package created at: {zip_path}")
    print(f"Total size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    package()
