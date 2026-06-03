import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.database import get_db
from api.models import User, Monitor, PingLog
from api.schemas import MonitorCreate, MonitorResponse, PingLogResponse
from api.routers.auth import get_current_user

router = APIRouter(prefix="/monitors", tags=["Infrastructure Monitors"])

@router.post("", response_model=MonitorResponse, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    monitor_in: MonitorCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if monitor_in.monitor_type == "HTTP" and not monitor_in.target_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Target URL is strictly required for HTTP tracking parameters"
        )
        
    new_monitor = Monitor(
        user_id=current_user.id,
        name=monitor_in.name,
        monitor_type=monitor_in.monitor_type,
        target_url=monitor_in.target_url,
        check_interval_seconds=monitor_in.check_interval_seconds
    )
    db.add(new_monitor)
    await db.flush()
    return new_monitor

@router.get("", response_model=list[MonitorResponse])
async def list_monitors(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = select(Monitor).where(Monitor.user_id == current_user.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == current_user.id)
    result = await db.execute(query)
    monitor = result.scalars().first()
    
    if not monitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target monitor config not found")
        
    await db.delete(monitor)

@router.get("/{monitor_id}/logs", response_model=list[PingLogResponse])
async def get_monitor_metrics(
    monitor_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Verify owner permissions before exposing history logs
    query = select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == current_user.id)
    monitor_check = await db.execute(query)
    if not monitor_check.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target monitor config not found")

    logs_query = select(PingLog).where(PingLog.monitor_id == monitor_id).order_by(PingLog.checked_at.desc()).limit(100)
    logs_result = await db.execute(logs_query)
    return logs_result.scalars().all()
