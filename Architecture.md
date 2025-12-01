# Architecture Description 

## 1. Controller Component

### 1.1 Role
The Controller serves as the primary orchestrator of the system. It mediates all user-driven actions and coordinates interactions between the Capture Module and ChatBot. The Controller observes GUI-emitted events and processes them in a background thread.

### 1.2 Responsibilities
- Observe GUI events and translate them into module actions.
- Forward user-initiated commands to the appropriate modules.
- Route pre-determined user queries to the ChatBot.

### 1.3 Interfaces
**Events In (from GUI):**
- `start_capture(CaptureConfig)`
- `stop_capture()`
- `query_raised(QueryMessage)`

**Commands Out (to Capture Module):**
- `start_capture(config: CaptureConfig)`
- `stop_capture()`

**Queries to ChatBot:**
- `process_query(text)`

### 1.4 Relationships
- **Controller ← GUI:** Receives events (user intent).
- **Controller → Capture Module:** Issues operational directives.
- **Controller ↔ ChatBot:** Sends queries.


## 2. Capture Module

### 2.1 Role
The Capture Module is responsible for real-time acquisition of network packets according to the parameters specified by the Controller.

### 2.2 Responsibilities
- Capture network packets filtered by protocol and port (configured dynamically via `CaptureConfig`).
- Emit packet capture events for downstream processing.

### 2.3 Events Produced
**`packet_captured(packet_data)`**  
Contains raw packet metadata and payload summary.

### 2.4 Relationships
**Receives:**
- Commands from Controller.

**Sends:**
- **Capture Module → Metrics Module:** `packet_captured` events.
- **Capture Module → GUI:** `packet_captured` events.


## 3. Metrics Module

### 3.1 Role
The Metrics Module computes all quantitative system metrics based on incoming packets.

### 3.2 Responsibilities
- Receive packet events and update internal statistical models.
- Compute metrics such as total packets, throughput, average packet size, packet rate, and latency.
- Emit metric update events to dependent modules.

### 3.3 Events Produced
**`metrics_updated(metrics_snapshot)`**  
Contains the latest computed metrics.

### 3.4 Relationships
**Receives:**
- From Capture Module: `packet_captured`

**Sends:**
- **Metrics Module → Alert Module:** `metrics_updated`
- **Metrics Module → GUI Module:** `metrics_updated`


## 4. Alert Module

### 4.1 Role
The Alert Module performs rule-based and threshold-based evaluation of both raw packet data and computed metrics.

### 4.2 Responsibilities
- Evaluate incoming metrics for anomaly conditions.
- Trigger alerts when thresholds are exceeded.
- Forward alert events to the GUI for user visibility.

### 4.3 Events Produced
**`alert_generated(alert_info)`**  
Represents high latency, traffic spike, or any threshold violation.

### 4.4 Relationships
**Receives:**
- From Metrics Module: `metrics_updated`

**Sends:**
- **Alert Module → GUI Module:** `alert_generated`


## 5. GUI Module

### 5.1 Role
The GUI Module provides the visual user interface for real-time monitoring, data inspection, and interactive querying. It acts as a Boundary in the ECB pattern and is both a Subject (publishes user intent) and an Observer (renders system updates).

### 5.2 Responsibilities
- Display capture status, live metrics, and active alerts.
- Present chatbot responses to user queries.
- Publish user intent via events (start/stop capture, chatbot queries) to decouple from Controller.

### 5.3 Events Consumed
- `metrics_updated`
- `alert_generated`
- `packet_captured`
- Indirectly reflects packet updates via the above events.

### 5.4 Relationships
**Receives:**
- From Metrics Module: `metrics_updated`
- From Alert Module: `alert_generated`
- From Controller: `packet_captured`

**Sends:**
- To Controller: User intent via events (`start_capture`, `stop_capture`, `query_raised`)


## 6. ChatBot Component

### 6.1 Role
The ChatBot provides a pre-determined requests interface for querying system state and retrieving insights.

### 6.2 Responsibilities
- Process user questions and extract intent.
- Retrieve required data from Metrics Module, Alert Module, and update GUI Module using direct method calls.

### 6.3 Relationships
**Receives:**
- From Controller: textual user queries.

### Direct Interactions (Pull-Based)
ChatBot interacts with modules through synchronous data-access methods such as:
- `metrics.get_current_values()`
- `alert_manager.get_active_alerts()`
- `gui.update()`

*Note: ChatBot does not participate in the observer event stream.*

## 7. Concurrency & Shutdown

- GUI runs on the main thread (CustomTkinter mainloop).
- Controller runs in a background thread, receiving GUI events via a thread-safe queue.
- Capture runs in its own daemon thread; `stop_capture()` force-closes pyshark capture to break blocking reads.
- On GUI close, the Controller is stopped and the app exits cleanly.

## 8. Decision Log (High-Level)

- 2025-11-29: Adopt CustomTkinter and `grid` for responsive GUI layout.
- 2025-11-29: Introduce event-driven GUI→Controller communication (Boundary as Subject).
- 2025-11-29: Implement graceful shutdown; daemonize capture thread and force-close pyshark on stop.
- 2025-11-29: Support Windows NPF interfaces by not filtering names containing "Device".