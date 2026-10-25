from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from database import SessionLocal, engine
from auth import router as auth_router
from lessons import router as lessons_router
from study import router as study_router
from seed_data import LESSONS, seed_words
from seed_english import ENGLISH

# Add the English course to the lesson content
LESSONS["en"] = ENGLISH

# Create the tables in lingo.db if they don't exist yet
models.Base.metadata.create_all(bind=engine)

# Load the lesson content into the database (adds only what is missing)
_db = SessionLocal()
try:
    seed_words(_db)
finally:
    _db.close()

app = FastAPI(title="Lingo API")

# Lets the frontend (served from another address) talk to this API.
# "*" is fine while developing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(lessons_router)
app.include_router(study_router)


@app.get("/")
def home():
    return {"message": "Lingo API is running"}