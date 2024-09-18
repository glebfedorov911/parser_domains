from pydantic_settings import BaseSettings
from pydantic import BaseModel
from pathlib import Path

import os  
from dotenv import load_dotenv


BASE_DIR = Path(__file__).parent.parent

DB_PATH = BASE_DIR / "db.sqlite3"

class DBSettings(BaseModel):
    url: str = f"sqlite+aiosqlite:///{DB_PATH}"
    echo: bool = False

class Templates(BaseModel):
    templates_path: Path = BASE_DIR / "templates"

class UploadDir(BaseModel):
    upload_path: Path = BASE_DIR / "upload"

class Docs(BaseModel):
    docs_path: Path = ""

class Settings(BaseSettings):
    db: DBSettings = DBSettings()
    template: Templates = Templates()
    upload: UploadDir = UploadDir()
    doc: Docs = Docs()

settings = Settings()

for not_exist in (settings.upload.upload_path, settings.template.templates_path):
    if not os.path.exists(not_exist):
        os.makedirs(not_exist)