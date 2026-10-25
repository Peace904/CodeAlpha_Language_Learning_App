from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(tags=["lessons"])

LANGUAGES = [
    {"code": "fr", "name": "French"},
    {"code": "es", "name": "Spanish"},
    {"code": "de", "name": "German"},
    {"code": "it", "name": "Italian"},
    {"code": "en", "name": "English"},
]


@router.get("/languages")
def list_languages():
    return LANGUAGES


@router.get("/words", response_model=List[schemas.WordOut])
def list_words(
    language: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Word).filter(models.Word.language == language)
    if category:
        query = query.filter(models.Word.category == category)
    return query.order_by(models.Word.id).all()