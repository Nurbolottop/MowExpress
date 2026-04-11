# RusCargo CRM

Веб‑приложение на Django для управления клиентами и заказами грузоперевозок (накладные, статусы, печать, аналитика).

## Возможности

- CRM для менеджера: логин, дашборд, профиль.
- Клиенты: создание, список, карточка клиента.
- Заказы:
  - создание/редактирование,
  - товарные позиции и дополнительные расходы,
  - итоговые расчёты,
  - быстрая смена статуса прямо в карточке заказа,
  - история смены статусов.
- Печать:
  - накладная (2 дубликата на одном листе A4),
  - самоклейка,
  - QR-код для страницы отслеживания.
- Настройки тарифов по весу:
  - «до X кг → цена за кг»,
  - автоподстановка цены при вводе веса в форме заказа.
- Страница трекинга для клиентов: `tracking/?code=...`.

## Технологии

- Python 3 / Django 5.2
- PostgreSQL 14
- Redis 6
- Docker / Docker Compose
- Gunicorn (prod)
- CKEditor

## Структура проекта

- `app/` — Django проект.
- `app/apps/base/` — CRM (вьюхи, формы, маршруты менеджера).
- `app/apps/logistics/` — доменная логика заказов и трекинг.
- `app/apps/users/` — клиенты/профили.
- `app/templates/` — HTML шаблоны CRM и печатных форм.
- `docker/` — `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`.
- `scripts/entrypoint.sh` — ожидание БД, миграции, collectstatic.
- `.envtest` — пример переменных окружения.

## Переменные окружения

Создайте `.env` на основе примера:

```bash
cp .envtest .env
```

Минимально проверьте:

- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `LANGUAGE_CODE`, `TIME_ZONE`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `POSTGRES_HOST` (должен совпадать с именем сервиса БД в compose)
- `POSTGRES_PORT`

## Запуск в разработке

```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

Сервисы dev:

- Django: `http://127.0.0.1:8084`
- Postgres: `5433`
- Redis: `6389`

После запуска можно выполнить миграции вручную (если нужно):

```bash
docker exec django_web_kgcargo python manage.py migrate
```

## Запуск в production-конфиге

```bash
docker-compose -f docker/docker-compose.prod.yml up -d --build
```

В этом режиме Django запускается через Gunicorn на `:8000`.

## Полезные команды

```bash
# Проверка проекта
docker exec django_web_kgcargo python manage.py check

# Создать суперпользователя
docker exec -it django_web_kgcargo python manage.py createsuperuser

# Логи web-контейнера
docker logs -f django_web_kgcargo
```

## Основные URL

- CRM: `/crm/`
- Заказы: `/crm/shipments/`
- Новый заказ: `/crm/shipments/create/`
- Настройки тарифов: `/crm/settings/`
- Трекинг: `/tracking/?code=<waybill_number>`

## Примечания

- Telegram-бот и интеграция Telegram из проекта удалены.
- В проекте может отображаться предупреждение по `django-ckeditor` (это не блокирующая ошибка запуска).
