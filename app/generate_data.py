import sys
from pathlib import Path

# Добавляем корневую папку в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import random
from datetime import datetime, timedelta
from faker import Faker
from tqdm import tqdm
from app.db import db
from app.config import config
from app.models import Employee, Ticket
from app.crud import EmployeeCRUD

fake = Faker("ru_RU")

async def generate_employees(count: int = 1000):
    """Генерация сотрудников"""
    departments = ["IT", "HR", "Sales", "Marketing", "Finance", "Operations", "R&D"]
    positions = ["Junior", "Middle", "Senior", "Lead", "Manager", "Director"]
    
    employees = []
    for _ in range(count):
        employee = Employee(
            full_name=fake.name(),
            department=random.choice(departments),
            position=random.choice(positions)
        )
        employees.append(employee)
    
    # Вставка батчами по 1000
    batch_size = 1000
    for i in range(0, len(employees), batch_size):
        batch = employees[i:i+batch_size]
        docs = [e.model_dump(by_alias=True, exclude={"id"}) for e in batch]
        await db.get_collection(config.COLL_EMPLOYEES).insert_many(docs)
    
    print(f"✅ Сгенерировано {count} сотрудников")

async def generate_tickets(count: int = 1_000_000):
    """Генерация заявок с уникальными номерами"""
    # Получаем ID всех сотрудников
    all_employees = await EmployeeCRUD.get_all(limit=10000)
    employee_ids = [str(emp.id) for emp in all_employees if emp.id]
    
    if not employee_ids:
        print("❌ Нет сотрудников для генерации заявок")
        return
    
    statuses = ["Новая", "В работе", "Выполнена"]
    
    # Генерация с прогресс-баром
    batch_size = 5000
    total_batches = (count + batch_size - 1) // batch_size
    
    print(f"📊 Генерация {count:,} заявок...")
    
    # Счетчик для уникальных номеров (максимум 999999)
    ticket_counter = 0
    
    for batch_num in tqdm(range(total_batches), desc="Генерация заявок"):
        batch_count = min(batch_size, count - batch_num * batch_size)
        tickets = []
        
        for _ in range(batch_count):
            # Увеличиваем счетчик
            ticket_counter += 1
            
            # Если счетчик превышает 999999, сбрасываем и добавляем префикс
            if ticket_counter > 999999:
                ticket_counter = 1
            
            # Формируем уникальный номер из 6 цифр
            ticket_number = f"TICKET-{ticket_counter:06d}"
            
            created_at = fake.date_time_between(start_date="-1y", end_date="now")
            deadline = created_at + timedelta(days=random.randint(1, 30))
            
            status = random.choice(statuses)
            executor_id = random.choice(employee_ids) if random.random() > 0.3 else None
            
            ticket = Ticket(
                number=ticket_number,
                created_at=created_at,
                author_id=random.choice(employee_ids),
                executor_id=executor_id,
                description=fake.text(max_nb_chars=200),
                deadline=deadline,
                status=status,
                updated_at=created_at + timedelta(hours=random.randint(1, 72))
            )
            tickets.append(ticket)
        
        # Вставка батча
        docs = [t.model_dump(by_alias=True, exclude={"id"}) for t in tickets]
        await db.get_collection(config.COLL_TICKETS).insert_many(docs)
    
    print(f"✅ Сгенерировано {count:,} заявок")

async def main():
    await db.connect()
    
    # Проверка наличия данных
    emp_count = await db.get_collection(config.COLL_EMPLOYEES).count_documents({})
    ticket_count = await db.get_collection(config.COLL_TICKETS).count_documents({})
    
    if emp_count > 0 or ticket_count > 0:
        response = input(f"⚠️ Найдено {emp_count} сотрудников и {ticket_count} заявок. Очистить? (y/n): ")
        if response.lower() == 'y':
            await db.get_collection(config.COLL_EMPLOYEES).drop()
            await db.get_collection(config.COLL_TICKETS).drop()
            print("🗑️ Старые данные удалены")
    
    await generate_employees(1000)
    await generate_tickets(1_000_000)
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())