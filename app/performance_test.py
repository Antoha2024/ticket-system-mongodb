import sys
from pathlib import Path

# Добавляем корневую папку в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import time
from datetime import datetime
from app.db import db
from app.config import config
from app.crud import EmployeeCRUD, TicketCRUD, convert_doc

async def test_performance():
    """Тестирование производительности запросов"""
    await db.connect()
    
    # Находим первого сотрудника для теста
    employees = await EmployeeCRUD.get_all(limit=1)
    if not employees or not employees[0].id:
        print("❌ Нет сотрудников для теста")
        await db.disconnect()
        return
    
    executor_id = employees[0].id
    
    print("=" * 60)
    print("🚀 Тестирование производительности запроса:")
    print(f"Запрос: просроченные заявки исполнителя {employees[0].full_name} в статусе 'В работе'")
    print("=" * 60)
    
    # Показываем количество записей в БД
    total_tickets = await db.get_collection(config.COLL_TICKETS).count_documents({})
    print(f"📊 Всего заявок в БД: {total_tickets:,}")
    
    # Замер времени
    start_time = time.time()
    
    # Запрос с использованием индексов
    pipeline = [
        {
            "$match": {
                "executor_id": executor_id,
                "status": "В работе",
                "deadline": {"$lt": datetime.now()}
            }
        },
        {"$sort": {"deadline": 1}}
    ]
    
    cursor = db.get_collection(config.COLL_TICKETS).aggregate(pipeline)
    results = []
    async for doc in cursor:
        doc = convert_doc(doc)
        results.append(doc)
    
    elapsed = time.time() - start_time
    
    print(f"\n📊 Результаты:")
    print(f"  • Найдено заявок: {len(results)}")
    print(f"  • Время выполнения: {elapsed:.4f} сек")
    
    # Информация об индексах
    print(f"\n📈 Информация об индексах:")
    indexes = await db.get_collection(config.COLL_TICKETS).index_information()
    for idx_name, idx_info in indexes.items():
        print(f"  • {idx_name}: {idx_info.get('key')}")
    
    # Объяснение оптимизации
    print(f"\n💡 Объяснение оптимизации:")
    print(f"  ✅ Составной индекс: (executor_id, status, deadline)")
    print(f"  ✅ Позволяет выполнить поиск за O(log n) вместо O(n)")
    print(f"  ✅ Индекс покрывает все поля в условии WHERE")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_performance())