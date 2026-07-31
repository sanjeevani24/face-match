import os
import shutil
import uuid


class FileUtils:

    @staticmethod
    def save_upload(file):
        uploads_dir = os.path.join(os.environ.get("DATA_DIR", "."), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        file_name = os.path.basename(file.filename)
        file_path = os.path.join(uploads_dir, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    @staticmethod
    def save_temp_upload(file):
        uploads_dir = os.path.join(os.environ.get("DATA_DIR", "."), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        ext = os.path.splitext(file.filename)[1] or ".jpg"
        file_path = os.path.join(uploads_dir, f"tmp_{uuid.uuid4().hex}{ext}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path