from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    language: str
    daily_goal: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class WordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language: str
    category: str
    text: str
    translation: str
    pronunciation: str
    note: str