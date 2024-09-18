from pydantic import BaseModel


class FileCreate(BaseModel):
    file: str