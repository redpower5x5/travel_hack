from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.orm import Session

from app.config import log
from app.schemas import response_schemas
from app.core.dependencies import get_db
from app.core import crud
from app.config import settings
from app.utils.token import get_current_active_user, get_current_active_admin

from fastapi_cache.decorator import cache
from typing import List

import time

router = APIRouter(
    prefix="/info",
    tags=["info"],
)


# get all statistics for all employees
@router.get("/statistics", response_model=response_schemas.EmployeeStatisticsList)
@cache(expire=settings.CACHE_EXPIRE)
async def get_all_statistics(
    department_ids: List[int] = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    current_user: response_schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get all stattistics with filters
    """
    log.debug(f"department_ids: {department_ids}, date_from: {date_from}, date_to: {date_to}")
    statistics = crud.get_user_statistics(db=db, department_ids=department_ids, date_from=date_from, date_to=date_to, user=current_user)

    if statistics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No statistics found",
        )

    return statistics

@router.get("/departments", response_model=response_schemas.DepartmentList)
@cache(expire=settings.CACHE_EXPIRE)
async def get_departments(
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_user),
):
    """
    Get all departmnets
    """
    departmnets = crud.get_all_departments(db=db, user=current_user)

    if departmnets is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No departments found",
        )

    return departmnets

@router.get("/periods", response_model=response_schemas.PeriodList)
@cache(expire=settings.CACHE_EXPIRE)
async def get_periods(
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_user),
):
    """
    Get all periods
    """
    periods = crud.get_all_periods(db=db, user=current_user)

    if periods is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No periods found",
        )

    return periods

@router.get("/employees/{id}", response_model=response_schemas.Employee)
@cache(expire=settings.CACHE_EXPIRE)
async def get_employee(
    id: int,
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_user),
):
    """
    Get employee by id
    """
    employee = crud.get_employee(db=db, id=id, user=current_user)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return employee