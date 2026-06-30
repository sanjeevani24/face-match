import cv2
import numpy as np
from insightface.app import FaceAnalysis


class FaceMatchAgent:

    def __init__(self):
        self.app = FaceAnalysis(
            providers=["CPUExecutionProvider"]
        )
        self.app.prepare(ctx_id=0)

    def get_embedding(self, image_path):
        image = cv2.imread(image_path)

        if image is None:
            raise Exception(f"Could not read image: {image_path}")

        faces = self.app.get(image)

        if len(faces) == 0:
            raise Exception(f"No face detected in image: {image_path}")

        return faces[0].embedding
        # embedding = faces[0].embedding
        # print(f"Embedding for {image_path}: {embedding}")
        # return embedding

    def compare_faces(self, aadhaar_image, selfie_image):
        emb1 = self.get_embedding(aadhaar_image)
        emb2 = self.get_embedding(selfie_image)

        similarity = np.dot(
            emb1 / np.linalg.norm(emb1),
            emb2 / np.linalg.norm(emb2)
        )

        return float(similarity)

    def verify_face(self, aadhaar_image, selfie_image):
        similarity = self.compare_faces(
            aadhaar_image,
            selfie_image
        )

        if similarity > 0.65:
            status = "MATCH"
        elif similarity > 0.55:
            status = "REVIEW"
        else:
            status = "NO_MATCH"

        return {
            "status": status,
            "similarity_score": round(similarity, 3)
        }
