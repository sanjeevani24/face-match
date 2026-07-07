import cv2
import numpy as np

from services.embedding_service import EmbeddingService

service = EmbeddingService()

image = cv2.imread("uploads/3.png")

embedding = service.extract(image)

print(type(embedding))

print(embedding.shape)

print(embedding[:10])

print(
    np.linalg.norm(embedding)
)