import cv2

from services.embedding_service import EmbeddingService
from services.similarity_service import SimilarityService


embedding_service = EmbeddingService()

# Same Person Images
image1 = cv2.imread("uploads/1.png")
image2 = cv2.imread("uploads/sample4_selfie.jpeg")

embedding1 = embedding_service.extract(image1)
embedding2 = embedding_service.extract(image2)

score = SimilarityService.cosine_similarity(
    embedding1,
    embedding2
)

print(f"Similarity Score : {score:.4f}")