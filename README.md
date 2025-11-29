# Packet Watch – Intelligent Network Management

## 1. Introduction
Packet Watch is an intelligent network monitoring and analysis tool designed to provide real-time traffic insights, anomaly alerts, and an integrated chatbot assistant for basic network queries.  

As network traffic grows more complex, effective monitoring becomes essential. Packet Watch simplifies this by allowing users to capture protocol-specific traffic, view essential metrics, receive alerts, and interact with a user-friendly GUI.

## 2. Features

### 2.1 Protocol & Port-based Packet Capture
- Filter packets by protocol (TCP, UDP, ICMP)
- Capture traffic for a specific port
- Ensures only relevant packets are analyzed

### 2.2 Real-time Network Metrics
Displays essential metrics such as:
- Total packets captured  
- Total data transferred  
- Average packet size  
- Packet rate  
- Latency  

### 2.3 Automated Alerts
- Detects anomalies when thresholds are exceeded  
- Alerts for high latency, traffic spikes, unusual packet flow, etc.  

### 2.4 Built-in Chatbot Assistant
Responds to predefined user queries like:
- *“What’s the average latency?”*  
- *“Any alerts?”*  
- Helps users quickly retrieve key information

### 2.5 Local Data Storage
- Stores captured packets  
- Saves computed metrics  
- Logs alerts for later analysis  

### 2.6 User-Friendly GUI
- Clean, modern interface built with **CustomTkinter** (Tkinter-based)
- Responsive layout using `grid`  
- Real-time traffic view  
- Metrics dashboard  
- Integrated chatbot panel  

### 2.7 Event-Driven Orchestration (ECB)
- GUI acts as a Boundary (Subject + Observer)
- GUI publishes user-intent events: `start_capture`, `stop_capture`, `query_raised`
- Controller observes GUI events and orchestrates modules
- Metrics and Alerts push updates to GUI via observer events

## 3 Tools & Technologies

- **Languages & Libraries:** Python, `scapy`, `pyshark`, `numpy`
- **GUI Framework:** CustomTkinter (Tkinter)
- **Platform:** Windows

## 4 Architecture Overview (ECB)

- **Boundary:** GUI (CustomTkinter)
	- Publishes user intent via events: `StartCaptureEvent`, `StopCaptureEvent`, `QueryRaised`
	- Subscribes to system updates: `MetricsUpdatedEvent`, `AlertGeneratedEvent`, `PacketCapturedEvent`
- **Control:** Controller
	- Observes GUI events in a background thread and calls Capture/Chatbot
- **Entities:** Capture, Metrics, Alerts, Storage
	- Capture emits `PacketCapturedEvent`
	- Metrics emits `MetricsUpdatedEvent`
	- Alerts emits `AlertGeneratedEvent`

### Concurrency & Shutdown
- GUI mainloop runs on main thread
- Controller runs in a background thread, processes GUI events
- Capture runs in a daemon thread; `stop_capture()` force-closes pyshark to break blocking reads
- Application performs graceful shutdown on GUI close (controller stopped, capture closed)

## 5. License
This project is for academic use. Licensing can be added here if needed.

## 6. Contributions
Suggestions or improvements are welcome — feel free to open an issue or PR.

## 7. Development Decision Log

- 2025-11-29: Switch GUI from PySimpleGUI to CustomTkinter
	- Reason: Licensing concerns and desire for modern, themeable widgets.
	- Impact: Updated requirements, full GUI refactor to CustomTkinter with `grid`.

- 2025-11-29: Decouple GUI and Controller via event system
	- Reason: Improve modularity and testability; follow ECB Boundary pattern.
	- Implementation: Added `StartCaptureEvent`, `StopCaptureEvent`, `QueryRaised`; GUI acts as Subject; Controller observes in background thread.

- 2025-11-29: Threading & shutdown policy
	- Reason: Prevent hangs and ensure clean exit on GUI close.
	- Implementation: Capture thread set to daemon; `stop_capture()` force-closes pyshark; controller exposes `stop()` and is joined on exit.

- 2025-11-29: Windows interface detection
	- Reason: Support NPF interfaces like `\Device\NPF_{GUID}`.
	- Change: Removed previous filter that skipped interfaces containing "Device".

- 2025-11-29: Timestamp type consistency
	- Reason: Align alert timestamps across modules.
	- Change: `AlertInfo.timestamp` uses `datetime` and alerts use `datetime.now()`.

- 2025-11-29: GUI restyle and font palette
	- Reason: Improve visual hierarchy and use user-preferred fonts for readability.
	- Impact: New font palette (Open Sans / Noto Sans for UI, JetBrains/Fira/Roboto Mono for monospace), flatter card-style layout, updated colors and spacing.

- 2025-11-29: Interface UX — psutil-backed active-interface picker
	- Reason: Raw pyshark interface list is noisy and includes inactive/remote adapters.
	- Impact: GUI lists friendly labels (e.g., "Ethernet (192.168.1.10)") for active interfaces only; hides verbose OS device names.

- 2025-11-29: Resolve friendly label → real adapter before capture
	- Reason: Users need simple names while pyshark requires real device identifiers.
	- Impact: GUI builds mapping label→device_name and passes resolved name via CaptureConfig; Capture still falls back to auto-detect if none provided.

- 2025-11-29: Protocol & port normalization for BPF filters
	- Reason: BPF filter syntax is case-sensitive and port 0 semantics differ.
	- Impact: Protocol values lowercased before building BPF filters; port 0 treated as "any port" by GUI and capture code.

- 2025-11-29: Error reporting and safe fallbacks
	- Reason: Improve user feedback when psutil/pyshark/tshark unavailable or interface invalid.
	- Impact: Clearer UI alerts/log messages; fallback to Auto-detect mode when probe fails.

- 2025-11-29: Race avoidance when starting capture from GUI
	- Reason: Auto-detection during capture start could race with GUI selection and cause spurious "no active interface" errors.
	- Impact: Controller now starts capture using the resolved CaptureConfig passed from GUI to avoid racey auto-detection.