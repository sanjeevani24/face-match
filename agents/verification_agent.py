import cv2

from services.embedding_service import EmbeddingService
from services.similarity_service import SimilarityService


class VerificationAgent:

    def __init__(self):

        self.embedding = EmbeddingService()

    def get_confidence(self, similarity):

        if similarity >= 0.90:
            return "Very High"

        elif similarity >= 0.70:
            return "High"

        elif similarity >= 0.55:
            return "Medium"

        return "Low"

    def verify(self, aadhaar_face, live_face):

        aadhaar_embedding = self.embedding.extract(
            aadhaar_face
        )

        live_embedding = self.embedding.extract(
            live_face
        )

        similarity = SimilarityService.cosine_similarity(
            aadhaar_embedding,
            live_embedding
        )

        threshold = 0.55

        if similarity >= threshold:
            reason = "Face match successful"
        else:
            reason = "Face mismatch"

        return {
            "verified": similarity >= threshold,
            "similarity": round(similarity, 4),
            "threshold": threshold,
            "confidence": self.get_confidence(similarity),
            "reason": reason
        }