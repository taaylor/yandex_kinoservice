import spacy
from fastapi import FastAPI
from pydantic import BaseModel

# Загружаем модель spaCy для русского языка
nlp = spacy.load("ru_core_news_sm")

# Создаём приложение FastAPI
app = FastAPI()


# Модель для входных данных
class QueryRequest(BaseModel):
    query: str


# Функция анализа запроса
def analyze_query(query: str):
    doc = nlp(query.lower())
    # Списки жанров и тематик
    genres = ["комедия", "фантастика", "драма", "ужасы", "боевик"]
    themes = ["будущее", "любовь", "приключения", "война", "история"]

    # Проверяем наличие жанра и тематики
    found_genre = any(token.text in genres for token in doc)
    found_theme = any(token.text in themes for token in doc)

    return {"genre": found_genre, "theme": found_theme}


# Эндпоинт для обработки запросов
@app.post("/analyze")
async def process_query(request: QueryRequest):
    analysis = analyze_query(request.query)

    # Проверяем, достаточно ли данных
    if analysis["genre"] and analysis["theme"]:
        return {"message": "Ваш запрос принят! Я найду фильм по жанру и тематике."}
    elif not analysis["genre"] and not analysis["theme"]:
        return {"message": "Пожалуйста, уточните жанр и тематику фильма."}
    elif not analysis["genre"]:
        return {"message": "Пожалуйста, уточните жанр фильма."}
    else:
        return {"message": "Пожалуйста, уточните тематику фильма."}
