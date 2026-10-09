from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import uuid

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

EXERCISE_ROOT = PROJECT_ROOT / "exercise-data"
MANIFEST_FILE = EXERCISE_ROOT / "manifest.json"

REPORTS_DIR = PROJECT_ROOT / "reports"

CHANGE_REPORT_FILE = (
    REPORTS_DIR /
    "m4_change_report.json"
)

UNDO_FILE = (
    REPORTS_DIR /
    "m4_undo_record.json"
)

MARKER_FILE = (
    EXERCISE_ROOT /
    "m4-controlled-change.marker"
)

TEXT_FILE_RELATIVE = (
    "documents/daily_operations.txt"
)

INVOICE_FILE_RELATIVE = (
    "invoices/invoices.csv"
)

RENAMED_INVOICE_NAME = (
    "invoices.m4-test"
)


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def load_manifest():
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            "manifest.json was not found."
        )

    with open(
        MANIFEST_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    allowed_files = manifest.get(
        "allowed_files"
    )

    if not isinstance(
        allowed_files,
        list
    ):
        raise ValueError(
            "Manifest allowed_files is invalid."
        )

    return manifest


def safe_path(relative_path):
    root = EXERCISE_ROOT.resolve()

    target = (
        EXERCISE_ROOT /
        relative_path
    ).resolve()

    try:
        target.relative_to(root)

    except ValueError:
        raise ValueError(
            f"Unsafe path rejected: "
            f"{relative_path}"
        )

    return target


def verify_manifest_target(
    manifest,
    relative_path
):
    allowed_files = {
        Path(path).as_posix()
        for path in manifest[
            "allowed_files"
        ]
    }

    normalised = (
        Path(relative_path)
        .as_posix()
    )

    if normalised not in allowed_files:
        raise ValueError(
            f"Target is not manifested: "
            f"{relative_path}"
        )

    return safe_path(relative_path)


def sha256_file(file_path):
    hasher = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as file:
        while True:
            block = file.read(65536)

            if not block:
                break

            hasher.update(block)

    return hasher.hexdigest()


def write_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4
        )


def create_controlled_changes():
    manifest = load_manifest()

    text_file = verify_manifest_target(
        manifest,
        TEXT_FILE_RELATIVE
    )

    invoice_file = verify_manifest_target(
        manifest,
        INVOICE_FILE_RELATIVE
    )

    if not text_file.exists():
        raise FileNotFoundError(
            "daily_operations.txt "
            "is missing."
        )

    if not invoice_file.exists():
        raise FileNotFoundError(
            "invoices.csv is missing."
        )

    renamed_invoice = (
        invoice_file.parent /
        RENAMED_INVOICE_NAME
    ).resolve()

    root = EXERCISE_ROOT.resolve()

    try:
        renamed_invoice.relative_to(root)

    except ValueError:
        raise ValueError(
            "Renamed invoice target "
            "is outside exercise-data."
        )

    if renamed_invoice.exists():
        raise FileExistsError(
            "M4 renamed invoice test "
            "file already exists."
        )

    if MARKER_FILE.exists():
        raise FileExistsError(
            "M4 marker already exists. "
            "Run undo first."
        )

    run_id = str(uuid.uuid4())

    before_text_hash = (
        sha256_file(text_file)
    )

    before_invoice_hash = (
        sha256_file(invoice_file)
    )

    original_text = (
        text_file.read_text(
            encoding="utf-8"
        )
    )

    undo_record = {
        "run_id": run_id,

        "created_utc": utc_now(),

        "text_file": {
            "path":
                TEXT_FILE_RELATIVE,

            "original_content":
                original_text,

            "original_sha256":
                before_text_hash
        },

        "renamed_file": {
            "original_path":
                INVOICE_FILE_RELATIVE,

            "temporary_path":
                (
                    Path("invoices") /
                    RENAMED_INVOICE_NAME
                ).as_posix(),

            "original_sha256":
                before_invoice_hash
        },

        "marker_file":
            MARKER_FILE.name,

        "state":
            "changes_applied"
    }

    write_json(
        UNDO_FILE,
        undo_record
    )

    print()
    print(
        "Creating harmless M4 marker..."
    )

    MARKER_FILE.write_text(
        (
            "M4 CONTROLLED LAB CHANGE\n"
            f"Run ID: {run_id}\n"
            f"Created UTC: {utc_now()}\n"
        ),
        encoding="utf-8"
    )

    print(
        "Modifying synthetic "
        "daily_operations.txt..."
    )

    text_file.write_text(
        (
            original_text
            + "\n\n"
            + "M4 LAB TEST: "
            + "temporary controlled "
            + "change.\n"
        ),
        encoding="utf-8"
    )

    print(
        "Temporarily renaming "
        "disposable invoices.csv..."
    )

    invoice_file.rename(
        renamed_invoice
    )

    after_text_hash = (
        sha256_file(text_file)
    )

    renamed_invoice_hash = (
        sha256_file(
            renamed_invoice
        )
    )

    report = {
        "run_id": run_id,

        "created_utc": utc_now(),

        "state":
            "controlled_changes_applied",

        "operations": [
            {
                "operation":
                    "create_marker",

                "path":
                    MARKER_FILE.name
            },

            {
                "operation":
                    "modify_text_file",

                "path":
                    TEXT_FILE_RELATIVE,

                "before_sha256":
                    before_text_hash,

                "after_sha256":
                    after_text_hash
            },

            {
                "operation":
                    "rename_file",

                "original_path":
                    INVOICE_FILE_RELATIVE,

                "temporary_path":
                    (
                        Path("invoices") /
                        RENAMED_INVOICE_NAME
                    ).as_posix(),

                "before_sha256":
                    before_invoice_hash,

                "after_sha256":
                    renamed_invoice_hash
            }
        ]
    }

    write_json(
        CHANGE_REPORT_FILE,
        report
    )

    print()
    print(
        "Controlled changes completed."
    )

    print()
    print("Run ID:")
    print(run_id)

    print()
    print(
        "Change report:"
    )
    print(
        CHANGE_REPORT_FILE
    )

    print()
    print(
        "Undo record:"
    )
    print(
        UNDO_FILE
    )

    print()
    print(
        "Only exercise-data was changed."
    )


def undo_controlled_changes():
    if not UNDO_FILE.exists():
        print()
        print(
            "No M4 undo record found."
        )
        return

    with open(
        UNDO_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        undo = json.load(file)

    if undo.get(
        "state"
    ) == "restored":
        print()
        print(
            "This M4 run has "
            "already been restored."
        )
        return

    text_info = (
        undo["text_file"]
    )

    rename_info = (
        undo["renamed_file"]
    )

    text_file = safe_path(
        text_info["path"]
    )

    original_invoice = safe_path(
        rename_info[
            "original_path"
        ]
    )

    temporary_invoice = safe_path(
        rename_info[
            "temporary_path"
        ]
    )

    print()
    print(
        "Restoring controlled "
        "M4 changes..."
    )

    if temporary_invoice.exists():
        if original_invoice.exists():
            raise FileExistsError(
                "Original invoices.csv "
                "already exists. "
                "Undo stopped."
            )

        temporary_invoice.rename(
            original_invoice
        )

        print(
            "Invoice filename restored."
        )

    else:
        print(
            "Temporary renamed invoice "
            "file was not found."
        )

    text_file.write_text(
        text_info[
            "original_content"
        ],
        encoding="utf-8"
    )

    print(
        "Synthetic text file restored."
    )

    if MARKER_FILE.exists():
        MARKER_FILE.unlink()

        print(
            "M4 marker removed."
        )

    restored_text_hash = (
        sha256_file(text_file)
    )

    restored_invoice_hash = (
        sha256_file(
            original_invoice
        )
    )

    text_matches = (
        restored_text_hash
        ==
        text_info[
            "original_sha256"
        ]
    )

    invoice_matches = (
        restored_invoice_hash
        ==
        rename_info[
            "original_sha256"
        ]
    )

    undo["state"] = "restored"

    undo["restored_utc"] = (
        utc_now()
    )

    undo[
        "verification"
    ] = {
        "text_hash_restored":
            text_matches,

        "invoice_hash_restored":
            invoice_matches
    }

    write_json(
        UNDO_FILE,
        undo
    )

    print()
    print("=== Recovery Verification ===")

    print(
        "Text file hash restored:",
        text_matches
    )

    print(
        "Invoice file hash restored:",
        invoice_matches
    )

    if text_matches and invoice_matches:
        print()
        print(
            "M4 recovery verified."
        )

    else:
        print()
        print(
            "Warning: recovery "
            "verification failed."
        )


def show_status():
    print()
    print("=== M4 File Behaviour Status ===")

    print(
        "Exercise root:",
        EXERCISE_ROOT
    )

    print(
        "M4 marker exists:",
        MARKER_FILE.exists()
    )

    invoice = safe_path(
        INVOICE_FILE_RELATIVE
    )

    temporary = safe_path(
        (
            Path("invoices") /
            RENAMED_INVOICE_NAME
        ).as_posix()
    )

    print(
        "Original invoices.csv exists:",
        invoice.exists()
    )

    print(
        "Temporary invoice exists:",
        temporary.exists()
    )

    print(
        "Undo record exists:",
        UNDO_FILE.exists()
    )


def main():
    while True:
        print()
        print(
            "=== M4 Controlled File Behaviour ==="
        )

        print()
        print(
            "1. Apply controlled changes"
        )

        print(
            "2. Undo controlled changes"
        )

        print(
            "3. Show status"
        )

        print(
            "0. Exit"
        )

        print()

        choice = input(
            "Select option: "
        ).strip()

        try:
            if choice == "1":
                create_controlled_changes()

            elif choice == "2":
                undo_controlled_changes()

            elif choice == "3":
                show_status()

            elif choice == "0":
                print()
                print("Exiting.")
                break

            else:
                print()
                print(
                    "Invalid option."
                )

        except Exception as error:
            print()
            print(
                "Operation failed:"
            )
            print(error)


if __name__ == "__main__":
    main()