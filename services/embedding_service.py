from insightface.app import FaceAnalysis
import numpy as np


class EmbeddingService:

    def __init__(self):

        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"]
        )

        self.app.prepare(
            ctx_id=0,
            det_size=(640, 640)
        )

    def extract(self, image):

        faces = self.app.get(image)

        if len(faces) == 0:
            raise Exception("No face detected")

        face = max(
            faces,
            key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1])
        )

        embedding = face.embedding.astype(np.float32)

        embedding = embedding / np.linalg.norm(embedding)

        return embedding