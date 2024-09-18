from fastapi import APIRouter, UploadFile, File, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from core.models.db_helper import db_helper

from .crud import save_file


router = APIRouter(prefix="/file", tags=["File"])

@router.post("/download_file/")
async def download_file(session: AsyncSession = Depends(db_helper.session_depends), file: UploadFile = File(...)):
    return await save_file(session=session, file=file)