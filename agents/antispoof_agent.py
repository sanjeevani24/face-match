from services.antispoof_services import AntiSpoofService


class AntiSpoofAgent:

    def __init__(self):
        self.service = AntiSpoofService()

    def verify(self, image_path):

        return self.service.predict(
            image_path
        )