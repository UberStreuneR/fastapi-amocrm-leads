## Запуск проекта

- Клонировать в локальный репозиторий
- Создать внешнюю интеграцию в amoCRM
- Внешний url указать https://example.com
- Предоставить доступ: Все -- кликнуть
- В файл .dev.env вставить id интеграции, secret_key, auth_key, поля для CRM (сделка, контакт, компания, протестировать можно с дефолтными)
- Также вставить HOST_URL, куда вебхук будет отправлять POST запросы
- $ docker-compose up
