import cv2

from agents.verification_agent import VerificationAgent

agent = VerificationAgent()

image1 = cv2.imread("uploads/1.png")
image2 = cv2.imread("uploads/sample4_selfie.jpeg")

result = agent.verify(
    image1,
    image2
)

print(result)