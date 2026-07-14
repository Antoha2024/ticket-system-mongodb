import sys
from pathlib import Path

# Добавляем корневую папку в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.db import db
from app.config import config
from app.models import Employee, Ticket, TicketWithDetails

def convert_doc(doc):
    """Конвертирует ObjectId в строку для Pydantic"""
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

class EmployeeCRUD:
    @staticmethod
    async def create(employee: Employee) -> str:
        """Создание сотрудника"""
        result = await db.get_collection(config.COLL_EMPLOYEES).insert_one(
            employee.model_dump(by_alias=True, exclude={"id"})
        )
        return str(result.inserted_id)
    
    @staticmethod
    async def get_by_id(emp_id: str) -> Optional[Employee]:
        """Получение сотрудника по ID"""
        try:
            doc = await db.get_collection(config.COLL_EMPLOYEES).find_one(
                {"_id": ObjectId(emp_id)}
            )
            if doc:
                doc = convert_doc(doc)
                return Employee(**doc)
            return None
        except:
            return None
    
    @staticmethod
    async def get_all(limit: int = 1000) -> List[Employee]:
        """Получение всех сотрудников"""
        cursor = db.get_collection(config.COLL_EMPLOYEES).find().limit(limit)
        employees = []
        async for doc in cursor:
            doc = convert_doc(doc)
            employees.append(Employee(**doc))
        return employees
    
    @staticmethod
    async def get_by_department(department: str) -> List[Employee]:
        """Получение сотрудников по подразделению"""
        cursor = db.get_collection(config.COLL_EMPLOYEES).find(
            {"department": department}
        )
        employees = []
        async for doc in cursor:
            doc = convert_doc(doc)
            employees.append(Employee(**doc))
        return employees

class TicketCRUD:
    @staticmethod
    async def create(ticket: Ticket) -> str:
        """Создание заявки"""
        ticket_data = ticket.model_dump(by_alias=True, exclude={"id"})
        result = await db.get_collection(config.COLL_TICKETS).insert_one(ticket_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_by_id(ticket_id: str) -> Optional[Ticket]:
        """Получение заявки по ID"""
        try:
            doc = await db.get_collection(config.COLL_TICKETS).find_one(
                {"_id": ObjectId(ticket_id)}
            )
            if doc:
                doc = convert_doc(doc)
                return Ticket(**doc)
            return None
        except:
            return None
    
    @staticmethod
    async def get_with_details(ticket_id: str) -> Optional[TicketWithDetails]:
        """Получение заявки с деталями сотрудников"""
        try:
            doc = await db.get_collection(config.COLL_TICKETS).find_one(
                {"_id": ObjectId(ticket_id)}
            )
            if not doc:
                return None
            
            doc = convert_doc(doc)
            ticket = TicketWithDetails(**doc)
            
            # Загружаем данные автора
            if ticket.author_id:
                author = await EmployeeCRUD.get_by_id(ticket.author_id)
                ticket.author = author
            
            # Загружаем данные исполнителя
            if ticket.executor_id:
                executor = await EmployeeCRUD.get_by_id(ticket.executor_id)
                ticket.executor = executor
            
            return ticket
        except:
            return None
    
    @staticmethod
    async def update_status(ticket_id: str, new_status: str) -> bool:
        """Обновление статуса с проверкой"""
        ticket = await TicketCRUD.get_by_id(ticket_id)
        if not ticket:
            return False
        
        if not ticket.can_transition_to(new_status):
            return False
        
        result = await db.get_collection(config.COLL_TICKETS).update_one(
            {"_id": ObjectId(ticket_id)},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now()
                }
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_executor(ticket_id: str, executor_id: str) -> bool:
        """Обновление исполнителя"""
        # Проверяем существование исполнителя
        executor = await EmployeeCRUD.get_by_id(executor_id)
        if not executor:
            return False
        
        try:
            result = await db.get_collection(config.COLL_TICKETS).update_one(
                {"_id": ObjectId(ticket_id)},
                {
                    "$set": {
                        "executor_id": executor_id,
                        "updated_at": datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except:
            return False
    
    @staticmethod
    async def filter(
        status: Optional[str] = None,
        executor_id: Optional[str] = None,
        department: Optional[str] = None,
        overdue_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Ticket]:
        """Фильтрация заявок"""
        query = {}
        
        if status:
            query["status"] = status
        
        if executor_id:
            query["executor_id"] = executor_id
        
        if overdue_only:
            query["deadline"] = {"$lt": datetime.now()}
            query["status"] = {"$ne": config.STATUS_COMPLETED}
        
        # Если фильтр по подразделению - сначала находим сотрудников
        if department:
            employees = await EmployeeCRUD.get_by_department(department)
            employee_ids = [str(emp.id) for emp in employees if emp.id]
            if employee_ids:
                query["executor_id"] = {"$in": employee_ids}
            else:
                return []
        
        cursor = db.get_collection(config.COLL_TICKETS).find(query).skip(skip).limit(limit)
        tickets = []
        async for doc in cursor:
            doc = convert_doc(doc)
            tickets.append(Ticket(**doc))
        return tickets
    
    @staticmethod
    async def get_report() -> Dict[str, Any]:
        """Получение отчета по заявкам"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        status_stats = {}
        async for doc in db.get_collection(config.COLL_TICKETS).aggregate(pipeline):
            status_stats[doc["_id"]] = doc["count"]
        
        # Количество просроченных
        overdue_count = await db.get_collection(config.COLL_TICKETS).count_documents({
            "deadline": {"$lt": datetime.now()},
            "status": {"$ne": config.STATUS_COMPLETED}
        })
        
        # Количество выполненных по исполнителям
        completed_by_executor = []
        pipeline_executor = [
            {"$match": {"status": config.STATUS_COMPLETED}},
            {"$group": {
                "_id": "$executor_id",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 50}
        ]
        
        async for doc in db.get_collection(config.COLL_TICKETS).aggregate(pipeline_executor):
            if doc["_id"]:
                executor = await EmployeeCRUD.get_by_id(doc["_id"])
                executor_name = executor.full_name if executor else "Неизвестен"
            else:
                executor_name = "Без исполнителя"
            completed_by_executor.append({
                "executor_name": executor_name,
                "count": doc["count"]
            })
        
        return {
            "status_stats": status_stats,
            "overdue_count": overdue_count,
            "completed_by_executor": completed_by_executor
        }