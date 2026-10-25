import datetime

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, UniqueConstraint

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    language = Column(String, default="fr")   # fr, de, it, es
    daily_goal = Column(Integer, default=10)  # words to study per day


class Word(Base):
    """One item to learn: a word, a phrase or a grammar example."""

    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    language = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)  # vocabulary, phrases, grammar
    text = Column(String, nullable=False)                  # in the language being learned
    translation = Column(String, nullable=False)           # in English
    pronunciation = Column(String, default="")             # simple phonetic spelling
    note = Column(String, default="")                      # grammar tip or usage note


class Progress(Base):
    """How well one user knows one word."""

    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "word_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    times_correct = Column(Integer, default=0)
    times_wrong = Column(Integer, default=0)
    learned = Column(Boolean, default=False)
    last_seen = Column(Date, default=datetime.date.today)


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String, nullable=False)
    category = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    taken_at = Column(Date, default=datetime.date.today)


class StudyLog(Base):
    """One row per user per day studied, used for the streak."""

    __tablename__ = "study_log"
    __table_args__ = (UniqueConstraint("user_id", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    words_studied = Column(Integer, default=0)