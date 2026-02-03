from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str


from pydantic import BaseModel
from typing import Optional

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

    admin_id: Optional[int] = None
    restaurant_id: Optional[int] = None
