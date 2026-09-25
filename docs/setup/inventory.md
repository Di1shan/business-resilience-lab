# Lab Environment Inventory

## Host System

- Host operating system: macOS 27.0
- macOS build: 26A428
- Mac model/chip: Apple M2 Pro
- Host memory: 16 GB
- Virtualisation software: VMware Fusion Professional
- VMware Fusion version: 26H1 (25388279)

## Windows 11 ARM64 VM

- Purpose: Fictional business application and controlled simulator
- Operating system: Microsoft Windows 11 Pro
- OS version: 10.0.26200
- Build: 26200
- Architecture: ARM64-based PC
- RAM: 4 GB
- CPU allocation: 2 cores
- Virtual disk size: 64 GB
- Python version: 3.14.7
- Lab username: cyberlab

## Kali Linux ARM64 VM

- Purpose: Event receiver, Wireshark capture, and network analysis
- Operating system: Kali GNU/Linux Rolling
- Architecture: aarch64
- RAM: 4 GB
- CPU allocation: 2 cores
- Virtual disk size: 40 GB
- Python version: 3.14.6
- Wireshark version: 4.6.6

## Recovery

- Clean VMware snapshot created: Yes
- Snapshot name: Clean-Business-Lab
- Snapshot restoration test: Completed

## Notes

- Both virtual machines use the isolated/private VMware lab network.
- Python is installed and working on both virtual machines.
- Wireshark is installed and working on Kali Linux.
- Windows-to-Kali communication has been successfully tested.
- The lab is intended for synthetic and disposable project data only.
- VM images, snapshots, credentials, keys, tokens, and raw private logs are not stored in the Git repository.
