import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RegisterStep1(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterStep1":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class RegisterStep2(BaseModel):
    member1_display_name: str = Field(min_length=1, max_length=100)
    member2_display_name: str | None = Field(default=None, max_length=100)
    partner_email: EmailStr | None = None
    currency: str = Field(min_length=3, max_length=3)


class RegisterRequest(BaseModel):
    step1: RegisterStep1
    step2: RegisterStep2


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)
