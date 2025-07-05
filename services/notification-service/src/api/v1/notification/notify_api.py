from typing import Annotated

from api.v1.notification.schemas import SingleNotificationRequest, SingleNotificationResponse
from fastapi import APIRouter, Body, Depends
from services.notification_service import NotificationService, get_notification_service

router = APIRouter()


@router.post(path="single-notification", response_model=SingleNotificationResponse)
async def create_single_notification(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    request_body: Annotated[SingleNotificationRequest, Body()],
) -> SingleNotificationResponse:
    return await service.send_single_notification(request_body=request_body)
