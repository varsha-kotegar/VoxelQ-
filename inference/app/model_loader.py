import threading
from ultralytics import YOLO

class ModelLoader:
    _instance = None
    _lock = threading.Lock()
    _model = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelLoader, cls).__new__(cls)
            return cls._instance

    def get_model(self) -> YOLO:
        with self._lock:
            if self._model is None:
                # Load the YOLO model once
                self._model = YOLO("yolov8n.pt")
            return self._model

def get_shared_model() -> YOLO:
    return ModelLoader().get_model()
