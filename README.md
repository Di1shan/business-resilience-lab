# Business Resilience Lab

A personal cybersecurity project focused on understanding malware-like behaviour, business disruption, detection, and recovery in a controlled and isolated lab environment.

## Project Overview

This project uses two virtual machines running in VMware Fusion:

- **Windows 11 ARM64** – fictional business application and controlled behaviour simulator
- **Kali Linux ARM64** – event receiver, network monitoring, and traffic analysis

The project will simulate controlled changes to disposable business data and examine how those changes can be detected, contained, and recovered from.

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

## Planned Structure

```text
business-resilience-lab/
├── windows/
├── kali-server/
├── tests/
│   └── synthetic-fixtures/
├── docs/
│   ├── setup/
│   └── scenarios/
├── evidence/
│   └── sanitised/
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

## Safety and Scope

This project is designed only for an isolated personal cybersecurity lab.

- Only synthetic and disposable data is used
- Simulator actions are manually initiated
- Testing is restricted to the configured lab environment
- No credential theft, stealth, security-tool interference, or arbitrary remote command execution is implemented
- VM images, snapshots, private logs, credentials, keys, and tokens will not be committed to this repository

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
