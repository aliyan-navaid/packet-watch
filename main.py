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
    controller.start()