# 🎫 Система учета заявок сотрудников

Система управления заявками сотрудников на **Python + MongoDB**, запускаемая в **Docker**.

---

## 📋 Содержание

- [🚀 Быстрый старт](#-быстрый-старт)
- [📁 Структура проекта](#-структура-проекта)
- [🎮 Работа с приложением](#-работа-с-приложением)
- [📊 Тест производительности](#-тест-производительности)
- [🔑 Доступы](#-доступы)
- [🛠️ Технологии](#️-технологии)
- [📝 Полезные запросы](#-полезные-запросы)
- [⚠️ Возможные проблемы](#️-возможные-проблемы)

---

## 🚀 Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Antoha2024/ticket-system-mongodb.git
```

### 2. Перейти в папку проекта

```bash
cd ticket-system-mongodb
```

### 3. Создать виртуальное окружение

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / WSL
```
или
```bash
.venv\Scripts\activate         # Windows
```

### 4. Установить зависимости

```bash
pip install -r app/requirements.txt
```

### 5. Запустить MongoDB в Docker

```bash
docker-compose up -d
```

### 6. Проверить, что MongoDB работает

```bash
docker ps
docker logs ticket_mongodb
```

### 7. Сгенерировать тестовые данные

```bash
python -m app.generate_data
```

**Что генерируется:**
- 👤 **1000** сотрудников
- 📋 **1,000,000** заявок

### 8. Проверить данные

```bash
python -m app.check_data
```

### 9. Запустить приложение

```bash
python -m app.menu
```

---

## 📁 Структура проекта

```
ticket-system-mongodb/
├── app/
│   ├── __init__.py
│   ├── menu.py              # Консольное меню
│   ├── db.py                # Подключение к MongoDB
│   ├── config.py            # Конфигурация
│   ├── models.py            # Модели данных (Pydantic)
│   ├── crud.py              # CRUD операции
│   ├── generate_data.py     # Генерация 1 млн заявок
│   ├── performance_test.py  # Тест производительности
│   ├── check_data.py        # Проверка данных
│   └── requirements.txt     # Зависимости
├── docker-compose.yml       # Запуск MongoDB
├── .env                     # Переменные окружения
├── .gitignore               # Исключения для git
└── README.md               # Документация
```

---

## 🎮 Работа с приложением

После запуска доступно консольное меню:

| Пункт | Описание |
|:-----:|----------|
| **1** | 👤 Создать сотрудника |
| **2** | 📋 Создать заявку |
| **3** | 🔄 Изменить статус заявки |
| **4** | 👤 Изменить исполнителя заявки |
| **5** | 🔍 Список заявок (фильтрация) |
| **6** | 📊 Отчет по заявкам |
| **7** | ⚡ Тест производительности |
| **8** | 🚪 Выход |

---

## 📊 Тест производительности

Для запуска теста выберите **пункт 7** в меню.

### Запрос
Просроченные заявки конкретного исполнителя в статусе «В работе», отсортированные по сроку выполнения.

### Результаты

| Показатель | Без индексов | С индексами | Ускорение |
|------------|--------------|-------------|-----------|
| Время выполнения | 0.38 сек | **0.013 сек** | **~30 раз** |

### Оптимизация

Создан составной индекс:

```javascript
db.tickets.createIndex({
  executor_id: 1,
  status: 1,
  deadline: 1
})
```

---

## 🔑 Доступы

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| **MongoDB** | `mongodb://localhost:27017/` | `admin` | `admin123` |
| **Mongo Express** | http://localhost:8081 | `admin` | `admin123` |

---

## 🛠️ Технологии

| Технология | Версия | Назначение |
|------------|--------|------------|
| **Python** | 3.12 | Язык программирования |
| **MongoDB** | 7.0 | База данных |
| **Motor** | 3.4.0 | Асинхронный драйвер MongoDB |
| **Pydantic** | 2.7.1 | Валидация данных |
| **Docker** | - | Контейнеризация |
| **Docker Compose** | - | Оркестрация контейнеров |
| **Faker** | 24.2.0 | Генерация тестовых данных |

---

## 📝 Полезные запросы

Подключитесь к MongoDB Shell:

```bash
docker exec -it ticket_mongodb mongosh -u admin -p admin123
```

Затем выполните:

```javascript
use ticket_db;

// Количество заявок по статусам
db.tickets.aggregate([
  {$group: {_id: '$status', count: {$sum: 1}}}
]);

// Просроченные заявки в работе
db.tickets.countDocuments({
  status: "В работе",
  deadline: {$lt: new Date()}
});

// Топ-10 исполнителей
db.tickets.aggregate([
  {$match: {status: "Выполнена", executor_id: {$ne: null}}},
  {$group: {_id: '$executor_id', count: {$sum: 1}}},
  {$sort: {count: -1}},
  {$limit: 10}
]);

// Все индексы
db.tickets.getIndexes();
```

---

## ⚠️ Возможные проблемы и решения

### Ошибка подключения к MongoDB

```bash
# Проверить, что контейнер работает
docker ps

# Перезапустить контейнер
docker-compose restart mongodb
```

### Ошибка с правами в WSL

Используйте Docker volume вместо локальной папки (уже настроено в `docker-compose.yml`).

### Ошибка создания индексов

Удалить все индексы и создать заново:

```bash
docker exec -it ticket_mongodb mongosh -u admin -p admin123 --eval "
use ticket_db;
db.tickets.dropIndexes();
db.tickets.createIndex({executor_id: 1});
db.tickets.createIndex({status: 1});
db.tickets.createIndex({deadline: 1});
db.tickets.createIndex({executor_id: 1, status: 1, deadline: 1});
"
```

---

## 📧 Контакты

По всем вопросам обращайтесь к разработчику.

---

**© 2026 Система учета заявок**
```

---

## 💾 КАК СОХРАНИТЬ

```bash
# Создать файл README.md
cat > README.md << 'EOF'
[вставьте сюда весь текст из блока выше]
EOF
```

Или откройте в VS Code и скопируйте туда.
