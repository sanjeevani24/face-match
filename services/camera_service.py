import cv2


class CameraService:

    def __init__(self):

        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            raise Exception("Could not open camera")

    def read(self):

        return self.cap.read()

    def release(self):

        self.cap.release()