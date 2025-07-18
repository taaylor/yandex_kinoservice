from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

app = FastAPI()

# Порог сходства
THRESHOLD = 0.45


class QueryRequest(BaseModel):
    query: str


genres = ["комедия", "фантастика", "драма", "ужасы", "боевик"]
themes = ["будущее", "любовь", "приключения", "война", "история"]
genres_embeddings = model.encode(genres)
themes_embeddings = model.encode(themes)


# Функция анализа запроса
def analyze_query(query: str):

    query_embedding = model.encode(query)

    genre_similarities = cosine_similarity([query_embedding], genres_embeddings)
    theme_similarities = cosine_similarity([query_embedding], themes_embeddings)

    has_genre = bool(max(genre_similarities[0]) > THRESHOLD)
    has_theme = bool(max(theme_similarities[0]) > THRESHOLD)

    best_match_genres = genres[genre_similarities.argmax()]
    best_match_themes = themes[theme_similarities.argmax()]

    genres_scores = float(genre_similarities.max())
    theme_scores = float(theme_similarities.max())

    return {
        "genre": best_match_genres,
        "theme": best_match_themes,
        "has_genre": has_genre,
        "has_theme": has_theme,
        "genres_scores": genres_scores,
        "theme_scores": theme_scores,
    }


# Эндпоинт для обработки запросов
@app.post("/analyze")
async def process_query(request: QueryRequest):
    analyze = analyze_query(request.query)

    # Формируем ответ
    if analyze["has_genre"] and analyze["has_theme"]:
        analyze["status"] = "OK"
        return analyze
    elif analyze["has_genre"]:
        analyze["status"] = "Пожалуйста, уточните тематику фильма."
        return analyze
    elif analyze["has_theme"]:
        analyze["status"] = "Пожалуйста, уточните жанр фильма."
        return analyze
    else:
        analyze["status"] = "Пожалуйста, уточните жанр и тематику фильма."
        return analyze
