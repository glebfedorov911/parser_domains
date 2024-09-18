from fastapi import UploadFile

import os

from core.config import settings


def get_unique_filename(filename: str):
    if not os.path.exists(os.path.join(settings.upload.upload_path, filename)):
        return filename

    name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = name + f"_({counter})_" + ext
        if not os.path.exists(os.path.join(settings.upload.upload_path, new_filename)):
            return new_filename
        counter += 1

async def save_to_upload(file: UploadFile, file_path: str):
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())