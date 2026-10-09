# Business Resilience Lab

A personal cybersecurity project focused on understanding malware-like behaviour, business disruption, detection, and recovery in a controlled and isolated lab environment.

## Project Overview

This project uses two virtual machines running in VMware Fusion:

- **Windows 11 ARM64** – fictional business application and controlled behaviour simulator
- **Kali Linux ARM64** – event receiver, network monitoring, and traffic analysis

The project simulates controlled changes to disposable business data and examines how those changes can be detected, contained, and recovered from.

No live malware is used. All simulation activities are manually started and restricted to generated lab data.

## Project Goals

- Build a fictional business application using Python
- Create synthetic customer and invoice data
- Develop a controlled behaviour simulator
- Monitor file and network activity
- Build an integrity monitoring system
- Test defensive controls
- Implement backup and recovery procedures
- Measure disruption, detection, and recovery
- Document results and evidence

## Repository Structure

```text
business-resilience-lab/
├── windows/
│   ├── business_app.py
│   ├── setup_business.py
│   ├── business-data/
│   ├── exercise-data/
│   ├── simulator/
│   │   ├── main.py
│   │   ├── config.json
│   │   ├── discovery.py
│   │   └── file_behaviour.py
│   ├── monitoring/
│   ├── recovery/
│   ├── reports/
│   │   ├── m4_inventory.json
│   │   ├── m4_change_report.json
│   │   └── m4_undo_record.json
│   └── tests/
├── kali-server/
├── tests/
│   └── synthetic-fixtures/
├── docs/
│   ├── setup/
│   └── scenarios/
├── evidence/
│   └── sanitised/
│       ├── m0/
│       ├── m1/
│       ├── m2/
│       ├── m3/
│       └── m4/
└── README.md
```

## Current Status

### Milestone M0 – Environment Setup

Completed the initial isolated lab environment using VMware Fusion on macOS.

- Windows 11 ARM64 VM configured with Python
- Kali Linux ARM64 VM configured with Python and Wireshark
- Both VMs connected through a private VMware network
- Windows-to-Kali communication successfully tested
- External network isolation verified
- Clean VMware recovery snapshot created for the project
- Lab environment ready for development and testing

**Status:** Completed

### Milestone M1 – Fictional Business Dataset

Created the initial fictional business dataset on the Windows lab VM.

- Created the required project folder structure
- Built `setup_business.py` using `pathlib` and `csv`
- Generated fictional customer data
- Generated fictional invoice data
- Created the daily operations document with a `LAB DATA ONLY` label
- Verified invoice total: `855.50`
- Verified unpaid total: `375.50`
- Verified that rerunning the setup script does not overwrite existing files

**Status:** Completed

### Milestone M2 – Business Application

Built the fictional business management application on the Windows lab VM.

- Added a command-line menu
- Added customer listing
- Added invoice listing
- Added unpaid invoice total calculation using `Decimal`
- Added invoice payment updates
- Added temporary-file replacement and backup handling
- Added daily report generation
- Added basic CSV validation and readable error handling
- Verified invoice updates persist after restarting the application
- Restored the dataset to the original baseline after testing

**Status:** Completed

### Milestone M3 – Simulator Controls and Safety Boundaries

Built the controlled behaviour simulator and added safety and scope validation before introducing any disruptive file behaviour.

- Created a separate disposable `exercise-data` copy of the business dataset
- Added a manifest containing the allowed synthetic files
- Added a required lab marker
- Added simulator configuration using `config.json`
- Added a command-line simulator menu
- Added dry-run mode
- Added unique run IDs
- Added per-run JSON records
- Added simulator state logging
- Added maximum file-count validation
- Added maximum total-size validation
- Added maximum run-duration configuration
- Added path validation to prevent operations outside the exercise directory
- Added protection against path traversal and unsafe junction targets
- Added a harmless marker-file simulation module
- Added a safety countdown before file creation
- Added manual cancellation during the countdown
- Added cleanup restricted to files created by the current run
- Added protection against repeated cleanup
- Verified normal `business-data` remains unchanged

Boundary tests completed:

- Missing lab marker
- Exercise root outside the project
- Excessive file count
- Junction pointing outside the allowed exercise directory
- Repeated cleanup
- Cancellation before file creation

Sanitised screenshots and example run records are stored under:

```text
evidence/sanitised/m3/
```

**Status:** Completed

### Milestone M4 – Scoped File Discovery and Controlled File Behaviour

Completed scoped file discovery and reversible file-behaviour testing using only the disposable `exercise-data` dataset.

#### Scoped file discovery

Created `discovery.py` to:

- Read the allowed files from `manifest.json`
- Check only manifested exercise files
- Record each file's relative path, extension, and size
- Identify missing manifested files
- Identify unexpected CSV or TXT files
- Create a structured inventory report
- Keep absolute user paths out of the public report

Generated report:

```text
windows/reports/m4_inventory.json
```

The final clean discovery run confirmed that the expected manifested files were present and no unexpected exercise files were found.

#### Controlled file behaviour

Created `file_behaviour.py` to perform a small set of controlled and reversible changes inside `exercise-data`.

The test module:

- Created a harmless M4 marker file
- Modified one synthetic text file
- Temporarily renamed the disposable `invoices.csv`
- Calculated SHA-256 hashes before and after controlled changes
- Recorded the exact operations in a change report
- Created an undo record before performing the changes
- Restored the renamed invoice file
- Restored the original text-file contents
- Removed the M4 marker
- Verified restored files using their original SHA-256 hashes

Generated records:

```text
windows/reports/m4_change_report.json
windows/reports/m4_undo_record.json
```

Recovery verification confirmed:

- Text file hash restored successfully
- Invoice file hash restored successfully
- Temporary renamed file removed
- M4 marker removed
- Original `invoices.csv` restored

#### Business application exercise mode

Updated `business_app.py` with a separate exercise mode.

Normal mode:

```powershell
python business_app.py
```

uses:

```text
business-data/
```

Exercise mode:

```powershell
python business_app.py --exercise
```

uses:

```text
exercise-data/
```

This allowed the controlled file-behaviour test to demonstrate a predictable business interruption without modifying the normal business dataset.

During the M4 test:

- The exercise application worked normally before the controlled change
- The disposable `invoices.csv` was temporarily unavailable
- The application displayed a clear missing-file error
- The controlled changes were undone
- The exercise application worked normally again after recovery
- The normal `business-data` dataset continued to work unchanged

Sanitised evidence is stored under:

```text
evidence/sanitised/m4/
```

**Status:** Completed

## Next Milestone

### Milestone M5 – Kali Receiver and Windows-to-Kali JSON Communication

The next stage will add structured communication between the Windows simulator and the Kali VM.

Planned work includes:

- Creating a Kali-side JSON event receiver
- Defining a fixed event-message schema
- Sending simulator event metadata from Windows
- Validating received JSON
- Rejecting malformed or oversized requests
- Adding finite timeouts and bounded retries
- Preventing duplicate event counting
- Testing receiver unavailability
- Comparing received events with Wireshark traffic
- Recording sanitised evidence for a complete communication run

Only synthetic event metadata will be sent. The receiver will not execute remote commands or arbitrary code.

**Status:** Not Started

## Safety and Scope

This project is designed only for an isolated personal cybersecurity lab.

- Only synthetic and disposable data is used
- Simulator actions are manually initiated
- Testing is restricted to the configured lab environment
- The simulator operates only on the disposable `exercise-data` dataset
- The normal `business-data` dataset remains separate
- Paths are validated before simulator operations
- Controlled file changes are reversible and recorded
- Recovery is verified using file hashes
- No credential theft, stealth, security-tool interference, or arbitrary remote command execution is implemented
- VM images, snapshots, raw private logs, credentials, keys, and tokens will not be committed to this repository

## Technologies

- Python 3
- VMware Fusion
- Windows 11 ARM64
- Kali Linux ARM64
- Wireshark
- Git and GitHub

## Author

Dilshan Witharanage

Computer Science student specialising in Cyber Security.
