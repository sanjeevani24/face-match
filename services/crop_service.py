import cv2

class CropService:

    @staticmethod
    def crop_aadhaar_photo(image_path):

        image = cv2.imread(image_path)

        if image is None:
            raise Exception("Could not read Aadhaar image")

        h, w = image.shape[:2]

        # Aadhaar photo region (approximate)
        x1 = int(w * 0.02)
        y1 = int(h * 0.20)

        x2 = int(w * 0.35)
        y2 = int(h * 0.85)

        face_crop = image[y1:y2, x1:x2]

        import os
        uploads_dir = os.path.join(
            os.environ.get("DATA_DIR", "."),
            "uploads",
        )
        os.makedirs(uploads_dir, exist_ok=True)
        
        output_path = os.path.join(uploads_dir, "cropped_aadhaar_face.jpg")

        cv2.imwrite(output_path, face_crop)

        return output_path