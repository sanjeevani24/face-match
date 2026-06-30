import cv2
from insightface.app import FaceAnalysis

app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(ctx_id=0, det_size=(1024,1024))

img = cv2.imread("uploads/Screenshot 2026-06-30 at 4.56.24PM.png")

print(img.shape)

faces = app.get(img)

print("Faces:", len(faces))