from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class Employee(BaseModel):
    """Модель сотрудника"""
    id: Optional[str] = Field(alias="_id", default=None)
    full_name: str = Field(..., min_length=2, max_length=100)
    department: str = Field(..., min_length=2, max_length=50)
    position: str = Field(..., min_length=2, max_length=50)
    created_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class Ticket(BaseModel):
    """Модель заявки"""
    id: Optional[str] = Field(alias="_id", default=None)
    number: str = Field(..., pattern=r'^TICKET-\d{6}$')
    created_at: datetime = Field(default_factory=datetime.now)
    author_id: str
    executor_id: Optional[str] = None
    description: str = Field(..., min_length=10, max_length=500)
    deadline: datetime
    status: str = Field(default="Новая")
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    def can_transition_to(self, new_status: str) -> bool:
        from app.config import config
        allowed = config.STATUS_TRANSITIONS.get(self.status, [])
        return new_status in allowed

class TicketWithDetails(Ticket):
    author: Optional[Employee] = None
    executor: Optional[Employee] = None