from app.controller import Controller
from app.modules import Alerts, Capture, Chatbot, GUI, Metrics

if __name__=="__main__":
    alerts, capturer, chatbot, gui, metrics \
    = Alerts(), Capture(), Chatbot(), GUI(), Metrics()

    capturer.subscribe(metrics)
    capturer.subscribe(gui)
    metrics.subscribe(alerts)
    metrics.subscribe(gui)
    alerts.subscribe(gui)

    controller = Controller(capturer, chatbot, gui)
    
    # Subscribe Controller to GUI events (User Actions)
    gui.subscribe(controller)
    
    # Start Controller (Background Thread)
    controller.start()
    
    # Start GUI (Main Thread - Blocking)
    gui.run()

    # Stop Controller when GUI closes
    controller.stop()