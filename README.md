# 🌸 Telegram-бот для косметолога

Бот для записи на процедуры. Данные автоматически попадают в **Google Таблицу клиента** через Google Apps Script.

---

## 🖥️ Запуск на Windows (PowerShell)

```powershell
# 1. Активировать виртуальное окружение
.venv\Scripts\Activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить окружение
Copy-Item .env.example .env

# 4. Запустить 
python -m bot.main


🧰 Команды Docker, которые тебе нужны (для PowerShell)
Вот твой минимальный набор команд для работы с Docker в PowerShell:

docker-compose up --build
Запускает
проект. Собирает образы и запускает контейнеры.
Ctrl + C
Останавливает
проект (если запущен в foreground).

docker-compose down
Останавливает и удаляет
контейнеры.

docker-compose logs
Показывает
логи всех
контейнеров.

docker-compose logs bot
Показывает
логи только бота
.
docker-compose exec bot sh
Открывает
терминал внутри контейнера бота
(для отладки).

docker volume prune
Удаляет все неиспользуемые тома
(включая данные БД — будь осторожен!).

docker-compose up -d
Запускает контейнеры в
фоновом режиме
(detached).

docker ps
Показывает
список запущенных
контейнеров.

docker images
Показывает
список образов





## 🖥️ Запуск Linux / Ubuntu (терминал)


# 1. Активировать виртуальное окружение
source venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить окружение
cp .env.example .env

# 4. Запустить
python bot/main.py