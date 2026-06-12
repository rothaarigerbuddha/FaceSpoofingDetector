# Frontier Web — фронтенд + бэкенд в одном проекте

Единая сборка проекта: **Next.js**-фронтенд и **.NET 8 / SQLite**-бэкенд, объединённые
так, чтобы подниматься вместе одной командой через Docker Compose. Дополнительно есть
скрипт `run.sh`, который поднимает стек и сразу открывает **публичный туннель** —
сайт можно открыть в браузере с любого устройства без аренды домена и хостинга.

```
frontier-web/
├── frontend/            # Next.js 16 / React 19 (статьи, дашборд, авторизация)
├── backend/             # .NET 8 Web API, clean architecture, SQLite, JWT
├── docker-compose.yml   # поднимает фронт + бэк вместе
├── run.sh               # одна команда: стек + публичный cloudflared-туннель
├── .env.example         # настройки (JWT-ключ и т.п.)
└── README.md
```

## Как это связано

```
Браузер ──▶ Frontend (Next.js, :3000) ──▶ Backend (.NET API, :5160) ──▶ SQLite (blog.db)
```

Важная особенность: фронтенд обращается к API **со стороны сервера Next.js** (через
`axios` + cookies), а не из браузера. Браузер всегда общается только с фронтендом.
Поэтому при работе через туннель не возникает проблем с CORS — наружу достаточно
отдать один порт (3000).

---

## Вариант 1. Запуск с публичным туннелем (одна команда)

Нужен установленный **Docker** (Desktop или Engine). `cloudflared` скрипт скачает сам,
если его нет.

```bash
cd frontier-web
cp .env.example .env      # по желанию — поменяйте JWT_KEY
./run.sh
```

Скрипт соберёт образы, поднимет контейнеры и выведет публичный адрес вида
`https://<random>.trycloudflare.com` — открывайте его в браузере. `Ctrl+C` закрывает
туннель (контейнеры продолжают работать).

Остановить всё: `./run.sh down`

## Вариант 2. Только локально, без туннеля

```bash
cd frontier-web
docker compose up --build      # или: ./run.sh --no-tunnel
```

- Сайт:    http://localhost:3000
- API:     http://localhost:5160
- Swagger: http://localhost:5160/swagger

Остановить: `Ctrl+C`, затем `docker compose down`.

**Тестовый вход:** `admin` / `admin123`

---

## Публичный туннель вручную (cloudflared / ngrok)

`run.sh` использует Cloudflare-туннель автоматически, но при желании можно поднять
туннель самому — главное направлять его на **порт фронтенда (3000)**.

### Cloudflare (без регистрации)

```bash
# установка (один раз)
#   macOS:        brew install cloudflared
#   Linux:        скачать бинарь из релизов github.com/cloudflare/cloudflared
#   Windows:      winget install --id Cloudflare.cloudflared

cloudflared tunnel --url http://localhost:3000
```

Команда выдаст временный URL `https://<random>.trycloudflare.com`.

### ngrok (нужен бесплатный аккаунт + токен)

```bash
# установка: https://ngrok.com/download, затем один раз:
ngrok config add-authtoken <ВАШ_ТОКЕН>

ngrok http 3000
```

ngrok покажет публичный `https://<random>.ngrok-free.app`. Откройте этот адрес.

> Совет: для постоянного доступа (свой домен, без «случайных» адресов и лимитов)
> используйте *named tunnel* в Cloudflare или платный тариф ngrok. Но для проверки
> и демонстраций хватает бесплатных быстрых туннелей выше.

---

## Локальная разработка без Docker

Если удобнее запускать напрямую (с hot-reload), нужны **.NET 8 SDK** и **Node.js LTS**.

**Бэкенд** (терминал 1):
```bash
cd backend/FrontierWeb
dotnet run                 # http://localhost:5160
```

**Фронтенд** (терминал 2):
```bash
cd frontend
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:5160" > .env
npm install
npm run dev                # http://localhost:3000
```

База данных SQLite (`blog.db`) создаётся автоматически при первом старте бэкенда и
наполняется тестовыми данными (пользователь `admin/admin123` и пост «Hello, world!»).

---

## Что было «склеено» при объединении

Фронтенд и бэкенд изначально разрабатывались отдельно, поэтому для связки сделано:

1. **Адрес API для фронтенда** — задаётся через `NEXT_PUBLIC_API_BASE_URL`
   (в Docker → `http://backend:5160`, локально → `http://localhost:5160`).
2. **CORS на бэкенде** — в `backend/FrontierWeb/Program.cs` к разрешённым источникам
   добавлен порт фронтенда `http://localhost:3000` (раньше был только `5173`).
3. **next.config** — в `remotePatterns` добавлен хост `backend:5160`, чтобы Next.js мог
   оптимизировать картинки из API внутри Docker-сети.
4. **База данных** — устаревший закоммиченный `blog.db` со старой схемой удалён; EF Core
   создаёт актуальную схему и сидирует данные при старте. В Docker файл БД хранится в
   именованном томе `backend-data`, поэтому переживает пересборку образов.

## Эндпоинты API (основное)

| Метод | Путь | Описание |
|------|------|----------|
| GET  | `/posts` | список статей (`?q=&page=&pageSize=&published=`) |
| GET  | `/posts/{idOrSlug}` | одна статья |
| POST | `/auth/login` | вход, возвращает JWT |
| GET  | `/users`, `/roles`, `/permissions` | управление доступом |
| POST | `/uploads` | загрузка изображений |

## Примечания

- Конфигурация рассчитана на **локальный запуск / демонстрацию**. Для боевого
  размещения смените `JWT_KEY`, рассмотрите замену SQLite на PostgreSQL и поставьте
  HTTPS/reverse-proxy перед сервисами.
- Загруженные через `/uploads` изображения хранятся внутри контейнера бэкенда; чтобы
  они переживали пересборку, примонтируйте том к каталогу загрузок (по аналогии с БД).
