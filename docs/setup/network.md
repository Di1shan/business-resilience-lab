# Lab Network Configuration

## Network Mode

- Virtualisation platform: VMware Fusion Professional
- Network mode: Private to my Mac
- Purpose: Allow communication between the Windows and Kali VMs while keeping the lab isolated from normal external network access
- Additional NAT or bridged adapters: None
- Shared folders: Disabled
- Shared clipboard / drag-and-drop: Disabled where available

## Windows 11 VM

- Hostname: DESKTOP-88RSGR0
- IPv4 address: 172.16.204.133
- Subnet mask / prefix: 255.255.255.0 (/24)
- Network: 172.16.204.0/24
- Default gateway: None
- Network interface: vmxnet3 Ethernet Adapter
- Role: Fictional business application and controlled simulator
- Default external route: Not present

## Kali Linux VM

- Hostname: kali
- IPv4 address: 172.16.204.130
- Subnet mask / prefix: /24
- Network: 172.16.204.0/24
- Default route: None
- Lab interface: eth0
- Role: Event receiver, Wireshark capture, and network analysis
- Default external route: Not present

## VM-to-VM Connectivity Test

- Test type: Temporary Python HTTP server
- Server VM: Kali Linux
- Server IPv4 address: 172.16.204.130
- Client VM: Windows 11
- Client IPv4 address: 172.16.204.133
- Test port: 8000
- Test file: hello.txt
- Result: Successful
- HTTP response: 200 OK
- Test text received: lab connection works

## Wireshark Verification

- Capture performed on Kali interface: eth0
- Display filter used: tcp.port == 8000
- Source address: 172.16.204.133
- Destination address: 172.16.204.130
- Destination port: 8000
- Windows-to-Kali HTTP request observed
- Successful HTTP response observed

## External Isolation Check

- Both VMs are configured with the VMware private network.
- No additional NAT or bridged adapters are intentionally enabled.
- No default external route is present on either VM.
- External connectivity tests fail as expected.
- The Mac host remains reachable because Private to my Mac is a host-only network.

## Notes

- VM addresses are assigned by the current private VMware network and may change.
- Current IP addresses must be checked before each network-based test.
- Guest and host firewalls remain enabled.
- Only required lab services should be allowed through firewall rules.
- The lab is intended for synthetic and disposable project data only.
- The private VMware network provides host-only isolation but does not isolate the VMs from the Mac host itself.
