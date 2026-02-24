from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.auth.deps import require_admin
from app.db.database import get_db
from app.db.models.chat_report import ChatReport
from app.db.models.chat_message import ChatMessage
from app.db.models.item import Item
from app.db.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


def _now():
    return datetime.now(timezone.utc)


class UserMini(BaseModel):
    id: int
    email: str
    name: str
    surname: str


class ReportOut(BaseModel):
    id: int
    status: str
    reason: str
    details: Optional[str] = None
    created_at: str

    thread_id: int
    item_id: int
    item_title: Optional[str] = None
    item_status: Optional[str] = None
    item_image_url: Optional[str] = None

    reporter: UserMini
    reported: UserMini


class ChatMsgOut(BaseModel):
    id: int
    thread_id: int
    sender_id: int
    text: str
    created_at: str
    client_id: Optional[str] = None


class ReportDetailOut(ReportOut):
    messages: List[ChatMsgOut]


class DecisionIn(BaseModel):
    action: Literal["ban", "reject"]
    note: Optional[str] = None


@router.get("/reports", response_model=List[ReportOut])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    Reporter = aliased(User)
    Reported = aliased(User)

    q = (
        select(ChatReport, Item, Reporter, Reported)
        .join(Item, Item.id == ChatReport.item_id)
        .join(Reporter, Reporter.id == ChatReport.reporter_id)
        .join(Reported, Reported.id == ChatReport.reported_user_id)
        .order_by(ChatReport.created_at.desc())
    )

    rows = (await db.execute(q)).all()
    out: list[ReportOut] = []
    for (r, item, reporter, reported) in rows:
        out.append(
            ReportOut(
                id=r.id,
                status=r.status,
                reason=r.reason,
                details=r.details,
                created_at=r.created_at.isoformat(),
                thread_id=r.thread_id,
                item_id=r.item_id,
                item_title=item.title,
                item_status=getattr(item.status, "value", item.status),
                item_image_url=item.image_url,
                reporter=UserMini(
                    id=reporter.id,
                    email=reporter.email,
                    name=reporter.name,
                    surname=reporter.surname,
                ),
                reported=UserMini(
                    id=reported.id,
                    email=reported.email,
                    name=reported.name,
                    surname=reported.surname,
                ),
            )
        )
    return out


@router.get("/reports/{report_id}", response_model=ReportDetailOut)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    Reporter = aliased(User)
    Reported = aliased(User)

    row = (
        await db.execute(
            select(ChatReport, Item, Reporter, Reported)
            .join(Item, Item.id == ChatReport.item_id)
            .join(Reporter, Reporter.id == ChatReport.reporter_id)
            .join(Reported, Reported.id == ChatReport.reported_user_id)
            .where(ChatReport.id == report_id)
        )
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    r, item, reporter, reported = row

    msgs = (
        await db.scalars(
            select(ChatMessage)
            .where(ChatMessage.thread_id == r.thread_id)
            .order_by(ChatMessage.created_at.asc())
        )
    ).all()

    return ReportDetailOut(
        id=r.id,
        status=r.status,
        reason=r.reason,
        details=r.details,
        created_at=r.created_at.isoformat(),
        thread_id=r.thread_id,
        item_id=r.item_id,
        item_title=item.title,
        item_status=getattr(item.status, "value", item.status),
        item_image_url=item.image_url,
        reporter=UserMini(
            id=reporter.id,
            email=reporter.email,
            name=reporter.name,
            surname=reporter.surname,
        ),
        reported=UserMini(
            id=reported.id,
            email=reported.email,
            name=reported.name,
            surname=reported.surname,
        ),
        messages=[
            ChatMsgOut(
                id=m.id,
                thread_id=m.thread_id,
                sender_id=m.sender_id,
                text=m.text,
                created_at=m.created_at.isoformat(),
                client_id=m.client_id,
            )
            for m in msgs
        ],
    )


@router.post("/reports/{report_id}/decision", response_model=ReportOut)
async def decide_report(
    report_id: int,
    payload: DecisionIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    report = await db.scalar(select(ChatReport).where(ChatReport.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != "pending":
        raise HTTPException(status_code=409, detail="Report already decided")

    reported_user = await db.scalar(select(User).where(User.id == report.reported_user_id))
    if not reported_user:
        raise HTTPException(status_code=404, detail="Reported user not found")

    if payload.action == "ban":
        reported_user.is_banned = True
        report.status = "banned"
    else:
        report.status = "rejected"

    report.decided_at = _now()
    report.decided_by_admin_id = admin.id
    report.admin_note = payload.note

    await db.commit()

    # Build response
    item = await db.scalar(select(Item).where(Item.id == report.item_id))
    reporter = await db.scalar(select(User).where(User.id == report.reporter_id))

    return ReportOut(
        id=report.id,
        status=report.status,
        reason=report.reason,
        details=report.details,
        created_at=report.created_at.isoformat(),
        thread_id=report.thread_id,
        item_id=report.item_id,
        item_title=item.title if item else None,
        item_status=getattr(item.status, "value", item.status) if item else None,
        item_image_url=item.image_url if item else None,
        reporter=UserMini(
            id=reporter.id,
            email=reporter.email,
            name=reporter.name,
            surname=reporter.surname,
        )
        if reporter
        else UserMini(id=report.reporter_id, email="", name="", surname=""),
        reported=UserMini(
            id=reported_user.id,
            email=reported_user.email,
            name=reported_user.name,
            surname=reported_user.surname,
        ),
    )


class RoleIn(BaseModel):
    role: Literal["user", "admin"]


@router.patch("/users/{user_id}/role")
async def set_role(
    user_id: int,
    payload: RoleIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    u = await db.scalar(select(User).where(User.id == user_id))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.role = payload.role
    await db.commit()
    return {"ok": True}


class BanIn(BaseModel):
    is_banned: bool


@router.patch("/users/{user_id}/ban")
async def set_ban(
    user_id: int,
    payload: BanIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    u = await db.scalar(select(User).where(User.id == user_id))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.is_banned = payload.is_banned
    await db.commit()
    return {"ok": True}
