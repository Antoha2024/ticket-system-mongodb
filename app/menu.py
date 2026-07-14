import sys
from pathlib import Path

# Добавляем корневую папку в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
from datetime import datetime
from app.db import db
from app.crud import EmployeeCRUD, TicketCRUD
from app.models import Employee, Ticket
from app.performance_test import test_performance
import random

async def display_menu():
    """Основное меню"""
    while True:
        print("\n" + "=" * 50)
        print("📋 СИСТЕМА УЧЕТА ЗАЯВОК")
        print("=" * 50)
        print("1. 👤 Создать сотрудника")
        print("2. 📋 Создать заявку")
        print("3. 🔄 Изменить статус заявки")
        print("4. 👤 Изменить исполнителя заявки")
        print("5. 🔍 Список заявок (фильтрация)")
        print("6. 📊 Отчет")
        print("7. ⚡ Тест производительности")
        print("8. 🚪 Выход")
        print("=" * 50)
        
        choice = input("Выберите действие: ").strip()
        
        if choice == "1":
            await create_employee()
        elif choice == "2":
            await create_ticket()
        elif choice == "3":
            await update_ticket_status()
        elif choice == "4":
            await update_ticket_executor()
        elif choice == "5":
            await filter_tickets()
        elif choice == "6":
            await show_report()
        elif choice == "7":
            await test_performance()
        elif choice == "8":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор!")

async def create_employee():
    """Создание сотрудника"""
    print("\n--- Создание сотрудника ---")
    full_name = input("ФИО: ").strip()
    department = input("Подразделение: ").strip()
    position = input("Должность: ").strip()
    
    employee = Employee(full_name=full_name, department=department, position=position)
    emp_id = await EmployeeCRUD.create(employee)
    print(f"✅ Сотрудник создан. ID: {emp_id}")

async def create_ticket():
    """Создание заявки"""
    print("\n--- Создание заявки ---")
    
    # Выбираем автора
    employees = await EmployeeCRUD.get_all(limit=10)
    if not employees:
        print("❌ Сначала создайте сотрудников!")
        return
    
    print("\nСотрудники:")
    for i, emp in enumerate(employees[:10], 1):
        print(f"  {i}. {emp.full_name} ({emp.department}) - {emp.position}")
    
    try:
        author_idx = int(input("Выберите автора (номер): ")) - 1
        author = employees[author_idx]
    except (ValueError, IndexError):
        print("❌ Неверный выбор!")
        return
    
    # Исполнитель (можно оставить пустым)
    executor_idx = input("Выберите исполнителя (номер, Enter - пропустить): ")
    executor_id = None
    if executor_idx.strip():
        try:
            executor_id = str(employees[int(executor_idx) - 1].id)
        except (ValueError, IndexError):
            print("❌ Неверный выбор!")
            return
    
    description = input("Описание: ").strip()
    
    deadline_str = input("Срок выполнения (ГГГГ-ММ-ДД): ").strip()
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
    except ValueError:
        print("❌ Неверный формат даты!")
        return
    
    # Генерация номера
    ticket = Ticket(
        number=f"TICKET-{random.randint(100000, 999999):06d}",
        author_id=str(author.id),
        executor_id=executor_id,
        description=description,
        deadline=deadline,
        status="Новая"
    )
    
    ticket_id = await TicketCRUD.create(ticket)
    print(f"✅ Заявка создана. ID: {ticket_id}")

async def update_ticket_status():
    """Обновление статуса заявки"""
    print("\n--- Обновление статуса заявки ---")
    ticket_id = input("ID заявки: ").strip()
    new_status = input("Новый статус (Новая/В работе/Выполнена): ").strip()
    
    success = await TicketCRUD.update_status(ticket_id, new_status)
    if success:
        print("✅ Статус обновлен!")
    else:
        print("❌ Ошибка: статус не может быть изменен!")

async def update_ticket_executor():
    """Обновление исполнителя заявки"""
    print("\n--- Обновление исполнителя ---")
    ticket_id = input("ID заявки: ").strip()
    executor_id = input("ID нового исполнителя: ").strip()
    
    success = await TicketCRUD.update_executor(ticket_id, executor_id)
    if success:
        print("✅ Исполнитель обновлен!")
    else:
        print("❌ Ошибка: исполнитель не найден!")

async def filter_tickets():
    """Фильтрация заявок"""
    print("\n--- Фильтр заявок ---")
    print("Оставьте поле пустым для пропуска фильтра")
    
    status = input("Статус (Новая/В работе/Выполнена): ").strip() or None
    executor_id = input("ID исполнителя: ").strip() or None
    department = input("Подразделение: ").strip() or None
    overdue_only = input("Только просроченные (y/n): ").strip().lower() == 'y'
    
    tickets = await TicketCRUD.filter(
        status=status,
        executor_id=executor_id,
        department=department,
        overdue_only=overdue_only,
        limit=20
    )
    
    print(f"\n📋 Найдено заявок: {len(tickets)}")
    for ticket in tickets:
        print(f"  • {ticket.number} | {ticket.status} | Срок: {ticket.deadline.date()}")

async def show_report():
    """Отчет"""
    print("\n--- Отчет по заявкам ---")
    report = await TicketCRUD.get_report()
    
    print("\n📊 Статистика по статусам:")
    for status, count in report["status_stats"].items():
        print(f"  • {status}: {count}")
    
    print(f"\n⏰ Просроченных заявок: {report['overdue_count']}")
    
    print("\n🏆 Выполненные заявки по исполнителям (Топ-10):")
    for item in report["completed_by_executor"][:10]:
        print(f"  • {item['executor_name']}: {item['count']}")

async def main():
    """Точка входа"""
    await db.connect()
    await display_menu()
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())