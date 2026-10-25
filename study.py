import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from deps import get_current_user

router = APIRouter(tags=["study"])

LANGUAGE_CODES = {"fr", "es", "de", "it", "en"}


class ReviewIn(BaseModel):
    word_id: int
    correct: bool


class QuizResultIn(BaseModel):
    language: str
    category: str
    score: int = Field(ge=0)
    total: int = Field(ge=1)


class QuizResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language: str
    category: str
    score: int
    total: int
    taken_at: datetime.date


class SettingsIn(BaseModel):
    language: str
    daily_goal: int = Field(ge=1, le=100)


def log_study_day(db: Session, user_id: int, count: int = 0) -> None:
    """Mark today as a study day for this user (used for the streak)."""
    today = datetime.date.today()
    log = (
        db.query(models.StudyLog)
        .filter(models.StudyLog.user_id == user_id, models.StudyLog.date == today)
        .first()
    )
    if log is None:
        log = models.StudyLog(user_id=user_id, date=today, words_studied=0)
        db.add(log)
    log.words_studied = (log.words_studied or 0) + count


@router.post("/study/review")
def review_word(
    data: ReviewIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = db.query(models.Word).filter(models.Word.id == data.word_id).first()
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    progress = (
        db.query(models.Progress)
        .filter(models.Progress.user_id == user.id, models.Progress.word_id == word.id)
        .first()
    )
    if progress is None:
        progress = models.Progress(
            user_id=user.id, word_id=word.id, times_correct=0, times_wrong=0, learned=False
        )
        db.add(progress)

    if data.correct:
        progress.times_correct += 1
    else:
        progress.times_wrong += 1

    # A word counts as learned after 3 correct answers
    progress.learned = progress.times_correct >= 3
    progress.last_seen = datetime.date.today()

    log_study_day(db, user.id, 1)
    db.commit()

    return {
        "word_id": word.id,
        "learned": progress.learned,
        "times_correct": progress.times_correct,
        "times_wrong": progress.times_wrong,
    }


@router.get("/study/summary")
def study_summary(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    language = user.language
    today = datetime.date.today()

    total = db.query(models.Word).filter(models.Word.language == language).count()
    learned = (
        db.query(models.Progress)
        .join(models.Word, models.Progress.word_id == models.Word.id)
        .filter(
            models.Progress.user_id == user.id,
            models.Progress.learned.is_(True),
            models.Word.language == language,
        )
        .count()
    )

    log = (
        db.query(models.StudyLog)
        .filter(models.StudyLog.user_id == user.id, models.StudyLog.date == today)
        .first()
    )
    studied_today = log.words_studied if log else 0

    # Streak: consecutive study days, counting back from today (or yesterday)
    dates = {d for (d,) in db.query(models.StudyLog.date).filter(models.StudyLog.user_id == user.id).all()}
    day = today if today in dates else today - datetime.timedelta(days=1)
    streak = 0
    while day in dates:
        streak += 1
        day -= datetime.timedelta(days=1)

    results = (
        db.query(models.QuizResult)
        .filter(models.QuizResult.user_id == user.id, models.QuizResult.language == language)
        .all()
    )
    quiz_count = len(results)
    average = round(sum(r.score / r.total for r in results) / quiz_count * 100) if quiz_count else 0

    return {
        "language": language,
        "daily_goal": user.daily_goal,
        "words_total": total,
        "words_learned": learned,
        "studied_today": studied_today,
        "streak": streak,
        "quiz_count": quiz_count,
        "quiz_average": average,
    }


@router.post("/quiz/results", response_model=QuizResultOut, status_code=201)
def save_quiz_result(
    data: QuizResultIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if data.score > data.total:
        raise HTTPException(status_code=400, detail="Score cannot be higher than the total")

    result = models.QuizResult(
        user_id=user.id,
        language=data.language,
        category=data.category,
        score=data.score,
        total=data.total,
        taken_at=datetime.date.today(),
    )
    db.add(result)
    log_study_day(db, user.id, 0)
    db.commit()
    db.refresh(result)
    return result


@router.get("/quiz/results", response_model=List[QuizResultOut])
def list_quiz_results(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.QuizResult)
        .filter(models.QuizResult.user_id == user.id)
        .order_by(models.QuizResult.id.desc())
        .limit(10)
        .all()
    )


@router.put("/settings", response_model=schemas.UserOut)
def update_settings(
    data: SettingsIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if data.language not in LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail="Unknown language")

    user.language = data.language
    user.daily_goal = data.daily_goal
    db.commit()
    db.refresh(user)
    return user