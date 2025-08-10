from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    """User model with basic user information"""
    id: int
    name: str
    email: str
    address: Optional[str] = None  # New address field
    
    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            # Add any custom encoders if needed
        }
        
    def __str__(self) -> str:
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"
    
    def __repr__(self) -> str:
        return self.__str__()