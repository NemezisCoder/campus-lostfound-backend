from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_image_bytes, cosine_similarity
from app.db.database import get_db
from app.db.models.item import Item
from app.schemas.items import (
    SimilarItemMatch,
    SimilarByImageResponse,
    DeduplicateResponse,
    Item as ItemSchema,
)

# ✅ Require auth for similarity endpoints
# Adjust these imports to your actual project structure.
from app.auth.deps import get_current_user
from app.db.models.user import User


router = APIRouter(
    prefix="/search",
    tags=["search"],
)


@router.post("/similar-by-image", response_model=SimilarByImageResponse)
async def similar_by_image(
    file: UploadFile = File(...),
    top_k: int = Query(5, ge=1, le=50),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ✅ auth required
):
    """Find top-K similar items by uploaded image.

    - Requires authentication (future chat flow needs an account anyway).
    - Excludes user's own items (owner_id != current_user.id).
    - Uses deterministic lightweight embeddings (can be replaced with CLIP later).
    """
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    query_vec = embed_image_bytes(data)

    # ✅ Exclude user's own items
    res = await db.execute(
        select(Item).where(
            Item.embedding.is_not(None),
            Item.owner_id != current_user.id,
        )
    )
    items = list(res.scalars().all())

    matches: List[SimilarItemMatch] = []
    for it in items:
        if not it.embedding:
            continue

        sim = cosine_similarity(query_vec, it.embedding)
        if sim >= min_similarity:
            matches.append(
                SimilarItemMatch(
                    item=ItemSchema.model_validate(it),
                    similarity=sim,
                )
            )

    matches.sort(key=lambda x: x.similarity, reverse=True)
    matches = matches[:top_k]
    return SimilarByImageResponse(matches=matches)


@router.post("/deduplicate", response_model=DeduplicateResponse)
async def deduplicate(
    item_id: int,
    top_k: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.85, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ✅ auth required
):
    """Find possible duplicates for an existing item by its stored embedding.

    - Requires authentication.
    - Excludes user's own items from duplicates list.
    """
    res = await db.execute(select(Item).where(Item.id == item_id))
    base = res.scalar_one_or_none()

    if not base or not base.embedding:
        raise HTTPException(status_code=404, detail="Item not found or has no embedding")

    # ✅ Exclude user's own items
    res = await db.execute(
        select(Item).where(
            Item.embedding.is_not(None),
            Item.id != item_id,
            Item.owner_id != current_user.id,
        )
    )
    others = list(res.scalars().all())

    dupes: List[SimilarItemMatch] = []
    for it in others:
        if not it.embedding:
            continue

        sim = cosine_similarity(base.embedding, it.embedding)
        if sim >= min_similarity:
            dupes.append(
                SimilarItemMatch(
                    item=ItemSchema.model_validate(it),
                    similarity=sim,
                )
            )

    dupes.sort(key=lambda x: x.similarity, reverse=True)
    dupes = dupes[:top_k]
    return DeduplicateResponse(possible_duplicates=dupes)
