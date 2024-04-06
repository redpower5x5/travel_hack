from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, File, UploadFile

from sqlalchemy.orm import Session

from app.config import log
from app.schemas import response_schemas, request_schemas
from app.core.dependencies import get_db
from app.core import crud
from app.config import settings
from app.utils.token import get_current_active_user, get_current_active_admin
import asyncio
import os

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

@router.post("/upload/employeelist", response_model=response_schemas.ProcessingInfo)
async def upload_employeelist(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_admin),
):
    """
    Upload employee list
    """
    # check file extension
    if file.filename.split(".")[-1] != 'csv':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension is not allowed",
        )
    file_path = os.path.join(settings.UPLOAD_FOLDER, file.filename)
    # create upload folder if not exists
    if not os.path.exists(settings.UPLOAD_FOLDER):
        os.makedirs(settings.UPLOAD_FOLDER)
    # save file
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    background_tasks.add_task(crud.upload_employeelist, db=db, file_path=file_path, current_user=current_user)
    return {"status": "processing", "message": "File is being processed"}

@router.post("/upload/employe_metrics", response_model=response_schemas.ProcessingInfo)
async def upload_employe_metrics(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_admin),
):
    """
    Upload employee metrics
    """
    # check file extension
    if file.filename.split(".")[-1] != 'csv':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension is not allowed",
        )
    file_path = os.path.join(settings.UPLOAD_FOLDER, file.filename)
    # create upload folder if not exists
    if not os.path.exists(settings.UPLOAD_FOLDER):
        os.makedirs(settings.UPLOAD_FOLDER)
    # save file
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    background_tasks.add_task(crud.upload_employe_metrics, db=db, file_path=file_path, current_user=current_user)
    return {"status": "processing", "message": "File is being processed"}

@router.get("/employees", response_model=response_schemas.EmployeeList)
async def get_employees(
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_admin),
):
    """
    Get all employees
    """
    employees = crud.get_all_employees(db=db, user=current_user)

    if employees is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employees found",
        )

    return employees
