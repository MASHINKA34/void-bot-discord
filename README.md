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
  cogs/
    bunker.py               слэш-команды игры «Бункер»
    greetings.py            приветствие и автовыдача роли
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
```

## Требуемые права бота

`Manage Channels`, `Manage Roles`, `Manage Messages`, `Send Messages`, `Embed Links`.
Привилегированные интенты: `Server Members`, `Message Content`.

## Настройка данных

| Файл | Что редактировать |
| --- | --- |
| `bot/data/characters.json` | категории и варианты характеристик |
| `bot/data/scenarios.json` | заголовок, описание, цвет и картинка сценария |
| `bot/data/banned_words.txt` | слова через пробел или с новой строки |
