import numpy as np


class SimilarityService:

    @staticmethod
    def cosine_similarity(embedding1, embedding2):

        similarity = np.dot(
            embedding1,
            embedding2
        )

        return float(similarity)