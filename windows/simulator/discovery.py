from pathlib import Path
from datetime import datetime, timezone
import json

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

EXERCISE_ROOT = PROJECT_ROOT / "exercise-data"
MANIFEST_FILE = EXERCISE_ROOT / "manifest.json"

REPORTS_DIR = PROJECT_ROOT / "reports"
REPORT_FILE = REPORTS_DIR / "m4_inventory.json"

ALLOWED_EXTENSIONS = {".csv", ".txt"}


def load_manifest():
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError("manifest.json was not found.")

    with open(MANIFEST_FILE, "r", encoding="utf-8") as file:
        manifest = json.load(file)

    allowed_files = manifest.get("allowed_files")

    if not isinstance(allowed_files, list):
        raise ValueError("Manifest does not contain a valid allowed_files list.")

    return manifest


def safe_manifest_path(relative_path):
    exercise_root = EXERCISE_ROOT.resolve()
    target = (EXERCISE_ROOT / relative_path).resolve()

    try:
        target.relative_to(exercise_root)
    except ValueError:
        raise ValueError(
            f"Unsafe manifest path detected: {relative_path}"
        )

    return target


def build_inventory(manifest):
    inventory = []
    missing_files = []

    for relative_path in manifest["allowed_files"]:
        file_path = safe_manifest_path(relative_path)

        if not file_path.exists():
            missing_files.append(relative_path)

            inventory.append({
                "path": relative_path,
                "status": "missing"
            })

            continue

        if not file_path.is_file():
            inventory.append({
                "path": relative_path,
                "status": "invalid"
            })

            continue

        inventory.append({
            "path": Path(relative_path).as_posix(),
            "extension": file_path.suffix.lower(),
            "size_bytes": file_path.stat().st_size,
            "status": "present"
        })

    return inventory, missing_files


def find_unexpected_files(manifest):
    expected_files = {
        Path(path).as_posix()
        for path in manifest["allowed_files"]
    }

    unexpected_files = []

    for file_path in EXERCISE_ROOT.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.name in {
            "manifest.json",
            ".business_lab_marker"
        }:
            continue

        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        relative_path = (
            file_path.relative_to(EXERCISE_ROOT)
            .as_posix()
        )

        if relative_path not in expected_files:
            unexpected_files.append(relative_path)

    unexpected_files.sort()

    return unexpected_files


def save_report(
    inventory,
    missing_files,
    unexpected_files
):
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    report = {
        "generated_utc":
            datetime.now(timezone.utc).isoformat(),

        "exercise_root": "exercise-data",

        "inventory": inventory,

        "summary": {
            "manifest_entries": len(inventory),

            "present_files": sum(
                1
                for item in inventory
                if item["status"] == "present"
            ),

            "missing_files": missing_files,

            "unexpected_files":
                unexpected_files
        }
    }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=4
        )

    return report


def main():
    print()
    print("=== M4 Scoped File Discovery ===")
    print()

    try:
        manifest = load_manifest()

        inventory, missing_files = (
            build_inventory(manifest)
        )

        unexpected_files = (
            find_unexpected_files(manifest)
        )

        print("Manifested files:")
        print()

        for item in inventory:
            print(f"Path: {item['path']}")
            print(f"Status: {item['status']}")

            if item["status"] == "present":
                print(
                    f"Extension: "
                    f"{item['extension']}"
                )

                print(
                    f"Size: "
                    f"{item['size_bytes']} bytes"
                )

            print()

        print("=== Manifest Comparison ===")
        print()

        if missing_files:
            print("Missing files:")

            for path in missing_files:
                print(f"  - {path}")

        else:
            print("Missing files: none")

        print()

        if unexpected_files:
            print("Unexpected files:")

            for path in unexpected_files:
                print(f"  - {path}")

        else:
            print("Unexpected files: none")

        print()

        save_report(
            inventory,
            missing_files,
            unexpected_files
        )

        print("Inventory report saved to:")
        print(REPORT_FILE)

        print()
        print(
            "Discovery completed successfully."
        )

    except Exception as error:
        print()
        print("Discovery failed:")
        print(error)


if __name__ == "__main__":
    main()