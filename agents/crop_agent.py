from services.crop_service import CropService

class CropAgent:

    def crop_face(self, aadhaar_path):

        cropped_path = CropService.crop_aadhaar_photo(
            aadhaar_path
        )

        return cropped_path