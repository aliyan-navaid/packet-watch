# Architecture Description 

## 1. Controller Component

### 1.1 Role
The Controller serves as the primary orchestrator of the system. It mediates all user-driven actions and coordinates interactions between the Capture Module and ChatBot.

### 1.2 Responsibilities
- Forward user-initiated commands from the GUI to the appropriate modules.
- Route pre-determined user queries to the ChatBot.

### 1.3 Interfaces
**Commands Out (to Capture Module):**
- `start_capture(protocol, port)`
- `stop_capture()`

**Queries to ChatBot:**
- `process_query(text)`

### 1.4 Relationships
- **Controller → Capture Module:** Issues operational directives.
- **Controller ↔ ChatBot:** Sends queries.


## 2. Capture Module

### 2.1 Role
The Capture Module is responsible for real-time acquisition of network packets according to the parameters specified by the Controller.

### 2.2 Responsibilities
- Capture network packets filtered by protocol and port.
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
The GUI Module provides the visual user interface for real-time monitoring, data inspection, and interactive querying.

### 5.2 Responsibilities
- Display capture status, live metrics, and active alerts.
- Present chatbot responses to user queries.
- Forward user commands (start/stop capture, chatbot queries) to the Controller.

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
- To Controller: UI actions (start/stop capture, chatbot query submission)


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