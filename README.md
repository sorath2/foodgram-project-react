# praktikum_new_diplom
## Продуктовый помощник «Foodgram»

## Описание проекта
На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Технологии
Python, Django Rest Framework, PostgreSQL, gunicorn, nginx, Docker

## Шаблон наполнения env-файла
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=пароль для подключения к БД
DB_HOST=db
DB_PORT=5432
SECRET_KEY = 'ключ django проекта. файл settings.py'

## Запуск проекта на Docker-Compose
- Перед запуском у вас должен быть установлен Docker, Docker-Compose
Запуск файла docker-compose.yml

sudo docker compose up -d
- Миграции

sudo docker compose exec <name_web> python manage.py migrate
- Создание суперпользователя

sudo docker compose exec <name_web> python manage.py createsuperuser
- Статика

sudo docker compose exec <name_web> python manage.py collectstatic --no-input


## Запуск проекта на локальной машине:
- Клонировать репозиторий

- В директории infra файл example.env переименовать в .env и заполнить своими данными,
согласно шаблону выше.

- Создать и запустить контейнеры Docker, как указано выше.

## После запуска проект будут доступен по адресу: http://localhost/

## Документация к API доступна здесь http://localhost/api/docs/

В документации описаны возможные запросы к API и структура ожидаемых ответов. Для каждого запроса указаны уровни прав доступа.