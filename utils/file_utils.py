import os
import shutil


class FileUtils:

    @staticmethod
    def save_upload(file):

        uploads_dir = os.path.join(
            os.environ.get("DATA_DIR", "."),
            "uploads",
        )

        os.makedirs(
            uploads_dir,
            exist_ok=True
        )

        file_name = os.path.basename(
            file.filename
        )

        file_path = os.path.join(
            uploads_dir,
            file_name
        )

        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        return file_path