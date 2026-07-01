import cv2
import numpy as np

from antispoof.src.anti_spoof_predict import AntiSpoofPredict


class AntiSpoofService:

    def __init__(self):

        self.model = AntiSpoofPredict(0)

        self.model_path = (
            "antispoof/resources/anti_spoof_models/"
            "2.7_80x80_MiniFASNetV2.pth"
        )

    def predict(self, image_path):

        image = cv2.imread(image_path)

        if image is None:
            raise Exception("Could not read image")

        image = cv2.resize(image, (80, 80))

        prediction = self.model.predict(
            image,
            self.model_path
        )

        label = int(np.argmax(prediction))
        confidence = float(np.max(prediction))

        return {
            "is_live": label == 1,
            "confidence": round(confidence, 3)
        }