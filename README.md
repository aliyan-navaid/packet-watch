# Packet Watch – Intelligent Network Management

## 1. Introduction
Packet Watch is an intelligent network monitoring and analysis tool designed to provide real-time traffic insights, anomaly alerts, and an integrated chatbot assistant for basic network queries.  

As network traffic grows more complex, effective monitoring becomes essential. NetSentinel simplifies this by allowing users to capture protocol-specific traffic, view essential metrics, receive alerts, and interact with a user-friendly GUI.

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
- Clean, minimal interface made with **PySimpleGUI**
- Real-time traffic view  
- Metrics dashboard  
- Integrated chatbot panel  

## 3 Tools & Technologies

- **Languages & Libraries:** Python, `scapy`, `pyshark`, `numpy`
- **GUI Framework:** PySimpleGUI
- **Platform:** Windows

## 4. License
This project is for academic use. Licensing can be added here if needed.

## 5. Contributions
Suggestions or improvements are welcome — feel free to open an issue or PR.
