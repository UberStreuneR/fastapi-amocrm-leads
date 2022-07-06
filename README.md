## Запуск проекта

- Клонировать в локальный репозиторий
- Создать внешнюю интеграцию в amoCRM
- Внешний url указать https://example.com
- Предоставить доступ: Все -- кликнуть
- В файл .dev.env вставить id интеграции, secret_key и auth_key без кавычек
- $ docker-compose up

## Использование

- localhost:8000/docs
- Протестировать с следующими данными:

  id: 50346643
  is_company: true
  months: 6

  id: 50346643
  is_company: true
  months: 6

- В докер встроен volume для проекта, попробуйте поменять API_KEY в app/creds.json
