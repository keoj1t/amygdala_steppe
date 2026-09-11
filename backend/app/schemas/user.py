from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
