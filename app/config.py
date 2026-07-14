import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "ticket_db")
    
    COLL_EMPLOYEES = "employees"
    COLL_TICKETS = "tickets"
    
    STATUS_NEW = "Новая"
    STATUS_IN_PROGRESS = "В работе"
    STATUS_COMPLETED = "Выполнена"
    
    STATUS_TRANSITIONS = {
        STATUS_NEW: [STATUS_IN_PROGRESS],
        STATUS_IN_PROGRESS: [STATUS_COMPLETED],
        STATUS_COMPLETED: []
    }

config = Config()