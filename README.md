# Void Bot

Discord-бот на [disnake](https://docs.disnake.dev/): игра «Бункер», приветствие новичков
и фильтр запрещённых слов.

## Запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
python main.py
```

Токен и все ID сервера задаются в `.env` (см. `.env.example`).

## Структура

```
main.py                     точка входа
bot/
  client.py                 класс бота, загрузка расширений
  config.py                 настройки из окружения
  storage.py                настройки серверов, JSON с атомарной записью
  cogs/
    bunker.py               слэш-команды игры «Бункер»
    greetings.py            приветствие, автовыдача роли, /welcome
    moderation.py           фильтр запрещённых слов
    owner.py                load / unload / reload
  bunker/
    character.py            пул характеристик
    player.py               игрок и его карточка
    session.py              состояние партии, голосование
    story.py                сценарии катастрофы
    views.py                кнопки открытия характеристик и голосования
  data/
    characters.json         характеристики
    scenarios.json          сценарии
    welcome_gifs.txt        гифки для приветствия
    banned_words.txt        запрещённые слова
storage/guilds.json         настройки серверов, создаётся ботом (в .gitignore)
```

## Настройка приветствия

Задаётся прямо в Discord, отдельно для каждого сервера. Нужно право «Управление сервером».

| Команда | Действие |
| --- | --- |
| `/welcome show` | показать текущие канал и роль |
| `/welcome channel <канал>` | выбрать канал приветствий |
| `/welcome role <роль>` | выбрать роль для автовыдачи |
| `/welcome off <канал\|роль\|всё>` | отключить |
| `/welcome test` | отправить пример приветствия |

Значения `WELCOME_CHANNEL_ID` и `AUTOROLE_ID` из `.env` используются как умолчания
для серверов, где `/welcome` ещё не настраивали.

## Требуемые права бота

`Manage Channels`, `Manage Roles`, `Manage Messages`, `Send Messages`, `Embed Links`.
Привилегированные интенты: `Server Members`, `Message Content`.

## Настройка данных

| Файл | Что редактировать |
| --- | --- |
| `bot/data/characters.json` | категории и варианты характеристик |
| `bot/data/scenarios.json` | заголовок, описание, цвет и картинка сценария |
| `bot/data/banned_words.txt` | слова через пробел или с новой строки |
