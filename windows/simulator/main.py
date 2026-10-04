from pathlib import Path
from datetime import datetime, timezone
import json
import uuid
import time
import msvcrt


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

CONFIG_FILE = BASE_DIR / "config.json"
LOGS_DIR = PROJECT_ROOT / "logs"
RUNS_DIR = LOGS_DIR / "runs"


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

def load_config():
    """
    Load simulator settings from config.json.
    """

    if not CONFIG_FILE.exists():
        print("Error: config.json not found.")
        return None

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            config = json.load(file)

    except json.JSONDecodeError:
        print("Error: config.json is not valid JSON.")
        return None

    required_keys = {
        "exercise_root",
        "marker_file",
        "manifest_file",
        "max_files",
        "max_total_bytes",
        "max_run_seconds"
    }

    missing_keys = required_keys - config.keys()

    if missing_keys:
        print(
            "Error: config.json is missing: "
            + ", ".join(sorted(missing_keys))
        )
        return None

    if not isinstance(config["max_files"], int):
        print("Error: max_files must be an integer.")
        return None

    if not isinstance(config["max_total_bytes"], int):
        print("Error: max_total_bytes must be an integer.")
        return None

    if not isinstance(config["max_run_seconds"], int):
        print("Error: max_run_seconds must be an integer.")
        return None

    if config["max_files"] <= 0:
        print("Error: max_files must be greater than 0.")
        return None

    if config["max_total_bytes"] <= 0:
        print("Error: max_total_bytes must be greater than 0.")
        return None

    if config["max_run_seconds"] <= 0:
        print("Error: max_run_seconds must be greater than 0.")
        return None

    return config


def get_exercise_root(config):
    """
    Resolve the configured exercise-data directory.
    """

    return (PROJECT_ROOT / config["exercise_root"]).resolve()


# ---------------------------------------------------------
# Exercise validation
# ---------------------------------------------------------

def validate_exercise_root(exercise_root):
    """
    Ensure exercise-data remains inside the project.
    """

    project_root = PROJECT_ROOT.resolve()

    if exercise_root == project_root:
        print("Error: exercise root cannot be the project root.")
        return False

    if exercise_root == Path(exercise_root.anchor):
        print("Error: exercise root cannot be a drive root.")
        return False

    try:
        exercise_root.relative_to(project_root)

    except ValueError:
        print("Error: exercise root is outside the project directory.")
        return False

    return True


def load_manifest(exercise_root, config):
    """
    Load exercise-data manifest.json.
    """

    manifest_file = exercise_root / config["manifest_file"]

    if not manifest_file.exists():
        print("Error: manifest file is missing.")
        return None

    try:
        with manifest_file.open("r", encoding="utf-8") as file:
            manifest = json.load(file)

    except json.JSONDecodeError:
        print("Error: manifest.json is not valid JSON.")
        return None

    if "allowed_files" not in manifest:
        print("Error: manifest does not contain allowed_files.")
        return None

    if not isinstance(manifest["allowed_files"], list):
        print("Error: allowed_files must be a list.")
        return None

    return manifest


def validate_marker(exercise_root, config):
    """
    Confirm that the required lab marker exists.
    """

    marker_file = exercise_root / config["marker_file"]

    if not marker_file.exists():
        print("Error: lab marker file is missing.")
        return False

    if not marker_file.is_file():
        print("Error: lab marker is not a regular file.")
        return False

    return True


def validate_manifest_files(exercise_root, manifest):
    """
    Validate every file listed in the manifest.
    """

    for relative_path in manifest["allowed_files"]:

        if not isinstance(relative_path, str):
            print("Error: manifest contains a non-string path.")
            return False

        target = (exercise_root / relative_path).resolve()

        # Reject path traversal or junction/symlink escape.
        try:
            target.relative_to(exercise_root)

        except ValueError:
            print(f"Error: unsafe path in manifest: {relative_path}")
            return False

        if not target.exists():
            print(f"Error: manifested file is missing: {relative_path}")
            return False

        if not target.is_file():
            print(
                f"Error: manifested target is not a file: "
                f"{relative_path}"
            )
            return False

    return True


def validate_limits(exercise_root, manifest, config):
    """
    Enforce configured file-count and total-size limits.
    """

    allowed_files = manifest["allowed_files"]

    if len(allowed_files) > config["max_files"]:
        print("Error: exercise exceeds the maximum file count.")
        return False

    total_bytes = 0

    for relative_path in allowed_files:
        target = (exercise_root / relative_path).resolve()
        total_bytes += target.stat().st_size

    if total_bytes > config["max_total_bytes"]:
        print("Error: exercise exceeds the maximum total size.")
        return False

    return True


def validate_exercise(config):
    """
    Run all M3 safety checks before simulator use.
    """

    exercise_root = get_exercise_root(config)

    print("\nValidating exercise environment...")
    print("-" * 40)

    if not validate_exercise_root(exercise_root):
        return False

    if not exercise_root.exists():
        print("Error: exercise-data folder does not exist.")
        return False

    if not exercise_root.is_dir():
        print("Error: exercise-data is not a directory.")
        return False

    if not validate_marker(exercise_root, config):
        return False

    manifest = load_manifest(exercise_root, config)

    if manifest is None:
        return False

    if not validate_manifest_files(exercise_root, manifest):
        return False

    if not validate_limits(exercise_root, manifest, config):
        return False

    print("Exercise root: PASS")
    print("Marker file: PASS")
    print("Manifest: PASS")
    print("Manifested files: PASS")
    print("Configured limits: PASS")

    return True


# ---------------------------------------------------------
# Run IDs and global state log
# ---------------------------------------------------------

def create_run_id():
    """
    Generate a unique run identifier.
    """

    return str(uuid.uuid4())


def log_state(run_id, state, message):
    """
    Append a state change to simulator_runs.jsonl.
    """

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOGS_DIR / "simulator_runs.jsonl"

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "state": state,
        "message": message
    }

    with log_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


# ---------------------------------------------------------
# Per-run records
# ---------------------------------------------------------

def get_run_record_path(run_id):
    """
    Return the JSON record path for a run.
    """

    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    return RUNS_DIR / f"{run_id}.json"


def create_run_record(run_id, module_name):
    """
    Create a new per-run JSON record.
    """

    record = {
        "run_id": run_id,
        "module": module_name,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "state": "running",
        "created_files": [],
        "cleanup_status": "not_cleaned"
    }

    save_run_record(run_id, record)


def load_run_record(run_id):
    """
    Load one per-run JSON record.
    """

    run_file = get_run_record_path(run_id)

    if not run_file.exists():
        print("Error: run record does not exist.")
        return None

    try:
        with run_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        print("Error: run record contains invalid JSON.")
        return None


def save_run_record(run_id, record):
    """
    Save a per-run JSON record.
    """

    run_file = get_run_record_path(run_id)

    with run_file.open("w", encoding="utf-8") as file:
        json.dump(record, file, indent=4)


# ---------------------------------------------------------
# Dry run
# ---------------------------------------------------------

def dry_run_preview(config, run_id):
    """
    Preview actions without changing exercise files.
    """

    exercise_root = get_exercise_root(config)
    manifest = load_manifest(exercise_root, config)

    if manifest is None:
        return False

    planned_marker = exercise_root / f"run-{run_id}.marker"

    print("\nDry Run Preview")
    print("-" * 50)

    print("\nAllowed exercise files:")

    for relative_path in manifest["allowed_files"]:
        print(f"  READ ONLY: {relative_path}")

    print("\nPlanned harmless action:")
    print(f"  CREATE: {planned_marker.name}")

    print("\nProtected original dataset:")
    print(f"  NO CHANGE: {PROJECT_ROOT / 'business-data'}")

    print("\nDry run mode:")
    print("  No files will be created.")
    print("  No files will be modified.")
    print("  No files will be renamed.")
    print("  No files will be deleted.")

    return True


def run_dry_run(config, runtime):
    """
    Execute a read-only dry run.
    """

    run_id = create_run_id()

    runtime["run_id"] = run_id
    runtime["state"] = "running"

    create_run_record(run_id, "dry_run")

    log_state(
        run_id,
        "running",
        "Dry run started."
    )

    print("\nDry run started.")
    print(f"Run ID: {run_id}")

    if dry_run_preview(config, run_id):

        runtime["state"] = "completed"

        record = load_run_record(run_id)

        if record is not None:
            record["state"] = "completed"
            record["completed_utc"] = (
                datetime.now(timezone.utc).isoformat()
            )
            save_run_record(run_id, record)

        log_state(
            run_id,
            "completed",
            "Dry run completed. No files were changed."
        )

        print("\nDry run completed.")
        print("No files were changed.")

    else:

        runtime["state"] = "failed"

        record = load_run_record(run_id)

        if record is not None:
            record["state"] = "failed"
            save_run_record(run_id, record)

        log_state(
            run_id,
            "failed",
            "Dry run failed."
        )


# ---------------------------------------------------------
# Keyboard handling for safe countdown
# ---------------------------------------------------------

def clear_keyboard_buffer():
    """
    Remove leftover keyboard input before a countdown.
    """

    while msvcrt.kbhit():
        msvcrt.getwch()


def check_for_cancel_key():
    """
    Return True when the user presses 4.

    Extended keys such as arrow keys are consumed and ignored.
    """

    while msvcrt.kbhit():

        key = msvcrt.getwch()

        # Arrow/function keys use a two-character sequence.
        if key in ("\x00", "\xe0"):

            if msvcrt.kbhit():
                msvcrt.getwch()

            continue

        if key == "4":
            return True

    return False


def safety_countdown(seconds):
    """
    Run a one-line countdown.

    Pressing 4 cancels the run.
    """

    clear_keyboard_buffer()

    deadline = time.monotonic() + seconds
    last_displayed = None

    while True:

        remaining = deadline - time.monotonic()

        if remaining <= 0:
            print(
                "\rSafety delay: 0 second(s) remaining...   "
            )
            return False

        seconds_remaining = int(remaining) + 1

        if seconds_remaining != last_displayed:

            print(
                f"\rSafety delay: "
                f"{seconds_remaining} second(s) remaining...   ",
                end="",
                flush=True
            )

            last_displayed = seconds_remaining

        if check_for_cancel_key():
            print()
            return True

        time.sleep(0.05)


# ---------------------------------------------------------
# Harmless marker module
# ---------------------------------------------------------

def run_marker_module(config, runtime):
    """
    Create a harmless run marker inside exercise-data.

    The module is synchronous so menu input cannot interfere
    with the countdown.
    """

    exercise_root = get_exercise_root(config)

    # Revalidate immediately before the run.
    if not validate_exercise_root(exercise_root):
        runtime["state"] = "failed"
        return

    run_id = create_run_id()

    marker_name = f"run-{run_id}.marker"
    marker_path = (exercise_root / marker_name).resolve()

    runtime["run_id"] = run_id
    runtime["state"] = "running"

    create_run_record(
        run_id,
        "harmless_marker"
    )

    log_state(
        run_id,
        "running",
        "Harmless marker module started."
    )

    print("\nMarker module started.")
    print(f"Run ID: {run_id}")
    print("Press 4 during the countdown to cancel.")
    print()

    wait_seconds = min(
        10,
        config["max_run_seconds"]
    )

    cancelled = safety_countdown(wait_seconds)

    # -----------------------------------------------------
    # Cancellation
    # -----------------------------------------------------

    if cancelled:

        runtime["state"] = "failed"

        record = load_run_record(run_id)

        if record is not None:

            record["state"] = "failed"
            record["result"] = "cancelled"
            record["cancelled_utc"] = (
                datetime.now(timezone.utc).isoformat()
            )

            save_run_record(run_id, record)

        log_state(
            run_id,
            "failed",
            "Run cancelled by user before file creation."
        )

        print("\nRun cancelled safely.")
        print("No marker file was created.")
        print("No business data was changed.")

        return

    # -----------------------------------------------------
    # Final safety validation
    # -----------------------------------------------------

    try:
        marker_path.relative_to(exercise_root)

    except ValueError:

        runtime["state"] = "failed"

        record = load_run_record(run_id)

        if record is not None:
            record["state"] = "failed"
            record["result"] = "scope_validation_failed"
            save_run_record(run_id, record)

        log_state(
            run_id,
            "failed",
            "Marker target failed final scope validation."
        )

        print("Error: marker target failed scope validation.")
        return

    # Required marker must still exist.
    if not validate_marker(exercise_root, config):

        runtime["state"] = "failed"

        record = load_run_record(run_id)

        if record is not None:
            record["state"] = "failed"
            record["result"] = "lab_marker_missing"
            save_run_record(run_id, record)

        log_state(
            run_id,
            "failed",
            "Lab marker disappeared before execution."
        )

        print("Run stopped safely.")
        return

    if marker_path.exists():

        runtime["state"] = "failed"

        record = load_run_record(run_id)

        if record is not None:
            record["state"] = "failed"
            record["result"] = "marker_already_exists"
            save_run_record(run_id, record)

        log_state(
            run_id,
            "failed",
            "Run marker already exists."
        )

        print("Error: run marker already exists.")
        return

    # -----------------------------------------------------
    # Harmless file creation
    # -----------------------------------------------------

    marker_text = (
        "LAB DATA ONLY\n"
        f"Run ID: {run_id}\n"
        f"Created UTC: "
        f"{datetime.now(timezone.utc).isoformat()}\n"
        "Purpose: Harmless M3 simulator marker.\n"
    )

    marker_path.write_text(
        marker_text,
        encoding="utf-8"
    )

    record = load_run_record(run_id)

    if record is not None:

        record["created_files"].append(marker_name)
        record["state"] = "completed"
        record["completed_utc"] = (
            datetime.now(timezone.utc).isoformat()
        )

        save_run_record(run_id, record)

    runtime["state"] = "completed"

    log_state(
        run_id,
        "completed",
        "Harmless marker module completed."
    )

    print("\nHarmless marker module completed.")
    print(f"Created: {marker_name}")


# ---------------------------------------------------------
# Stop
# ---------------------------------------------------------

def show_stop_status():
    """
    Stop option used when no countdown is active.

    Active marker runs are cancelled directly by pressing 4
    during their safety countdown.
    """

    print("\nNo active run to stop.")
    print(
        "During a marker run, press 4 "
        "while the countdown is active."
    )


# ---------------------------------------------------------
# Cleanup
# ---------------------------------------------------------

def cleanup_run(config, run_id):
    """
    Delete only files recorded as created by this run.
    """

    if run_id is None:
        print("\nNo run is available to clean up.")
        return False

    exercise_root = get_exercise_root(config)

    record = load_run_record(run_id)

    if record is None:
        return False

    if record.get("module") == "dry_run":
        print("\nDry runs do not create files to clean.")
        return False

    if record.get("cleanup_status") == "cleaned":
        print("\nThis run has already been cleaned.")
        return False

    created_files = record.get(
        "created_files",
        []
    )

    if not created_files:
        print("\nThis run did not create any files.")
        return False

    print("\nCleanup Preview")
    print("-" * 40)

    for relative_path in created_files:
        print(f"  DELETE: {relative_path}")

    # Validate every cleanup target before deleting anything.
    validated_targets = []

    for relative_path in created_files:

        target = (
            exercise_root / relative_path
        ).resolve()

        try:
            target.relative_to(exercise_root)

        except ValueError:

            print(
                "Error: cleanup target is outside "
                f"exercise-data: {relative_path}"
            )
            return False

        expected_name = f"run-{run_id}.marker"

        if target.name != expected_name:

            print(
                f"Error: cleanup target does not "
                f"belong to this run: {relative_path}"
            )
            return False

        if target.suffix != ".marker":

            print(
                "Error: cleanup target is not a "
                f"marker file: {relative_path}"
            )
            return False

        validated_targets.append(
            (relative_path, target)
        )

    # Delete only after all targets passed validation.
    for relative_path, target in validated_targets:

        if target.exists():

            target.unlink()
            print(f"Deleted: {relative_path}")

        else:

            print(f"Already absent: {relative_path}")

    record["state"] = "cleaned"
    record["cleanup_status"] = "cleaned"
    record["cleaned_utc"] = (
        datetime.now(timezone.utc).isoformat()
    )

    save_run_record(
        run_id,
        record
    )

    print("\nCleanup completed.")

    return True


# ---------------------------------------------------------
# Status and menu
# ---------------------------------------------------------

def show_status(config, runtime):
    """
    Display current simulator status.
    """

    exercise_root = get_exercise_root(config)

    print("\nSimulator Status")
    print("-" * 40)

    print(f"State: {runtime['state']}")

    print(
        f"Run ID: "
        f"{runtime['run_id'] if runtime['run_id'] else 'None'}"
    )

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Exercise root: {exercise_root}")
    print(f"Marker file: {config['marker_file']}")
    print(f"Manifest file: {config['manifest_file']}")
    print(f"Max files: {config['max_files']}")
    print(f"Max total bytes: {config['max_total_bytes']}")
    print(f"Max run seconds: {config['max_run_seconds']}")


def show_menu():
    """
    Display simulator control menu.
    """

    print("\nControlled Behaviour Simulator")
    print("1. Dry run")
    print("2. Run one module")
    print("3. Show status")
    print("4. Stop")
    print("5. Cleanup")
    print("0. Exit")


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():
    """
    Main simulator entry point.
    """

    config = load_config()

    if config is None:
        return

    runtime = {
        "state": "idle",
        "run_id": None
    }

    if validate_exercise(config):
        runtime["state"] = "validated"

    else:
        runtime["state"] = "failed"
        print("\nSimulator stopped because validation failed.")
        return

    while True:

        show_menu()

        choice = input(
            "Enter your choice: "
        ).strip()

        # ---------------------------------------------
        # Option 1 - Dry run
        # ---------------------------------------------

        if choice == "1":

            run_dry_run(
                config,
                runtime
            )

        # ---------------------------------------------
        # Option 2 - Harmless marker
        # ---------------------------------------------

        elif choice == "2":

            run_marker_module(
                config,
                runtime
            )

        # ---------------------------------------------
        # Option 3 - Status
        # ---------------------------------------------

        elif choice == "3":

            show_status(
                config,
                runtime
            )

        # ---------------------------------------------
        # Option 4 - Stop
        # ---------------------------------------------

        elif choice == "4":

            show_stop_status()

        # ---------------------------------------------
        # Option 5 - Cleanup
        # ---------------------------------------------

        elif choice == "5":

            if cleanup_run(
                config,
                runtime["run_id"]
            ):

                runtime["state"] = "cleaned"

                log_state(
                    runtime["run_id"],
                    "cleaned",
                    "Run cleanup completed successfully."
                )

        # ---------------------------------------------
        # Option 0 - Exit
        # ---------------------------------------------

        elif choice == "0":

            print("Exiting simulator.")
            break

        else:

            print("Invalid choice.")


if __name__ == "__main__":
    main()
