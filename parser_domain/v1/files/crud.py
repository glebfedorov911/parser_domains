from fastapi import APIRouter, UploadFile, File, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from sqlalchemy import select

from core.models.db_helper import db_helper
from core.config import settings
from core.models.file import File

from .depends import get_unique_filename, save_to_upload
from .schemas import FileCreate

import os


async def get_last_upload_file(session: AsyncSession):
    stmt = select(File)
    result: Result = await session.execute(stmt)

    return result.scalars().all()[-1]

async def save_file(session: AsyncSession, file: UploadFile):
    filename = get_unique_filename(file.filename)
    file_path = os.path.join(settings.upload.upload_path, filename)

    file_to_db = FileCreate(file=file_path)
    file_to_db = File(**file_to_db.model_dump())
    session.add(file_to_db)
    await session.commit()

    await save_to_upload(file=file, file_path=file_path)

    return await get_last_upload_file(session=session)