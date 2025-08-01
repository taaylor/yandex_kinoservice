import logging
from typing import Any

import dotenv
from core.logger_config import LoggerSettings
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = dotenv.find_dotenv()


class LLM(BaseModel):
    protocol: str = "http"
    host: str = "localhost"
    port: int = 11434
    path: str = "/api/generate"
    model: str = "llama3"
    timeout: int = 120

    @property
    def get_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{self.path}"

    resp_format: dict[str, Any] = {
        "type": "object",
        "properties": {
            "genre": {
                "type": ["string", "null"],
                "description": "Выбранный жанр или null, если жанр не указан.",
            },
            "theme": {
                "type": ["string", "null"],
                "description": "Выбранная тематика или null, если тематика не указана.",
            },
            "has_genre": {"type": "boolean", "description": "True, если жанр указан, иначе false."},
            "has_theme": {
                "type": "boolean",
                "description": "True, если тематика указана, иначе false.",
            },
            "genres_scores": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Максимальное значение косинусного сходства для жанра (от 0 до 1).",
            },
            "theme_scores": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Максимальное значение косинусного сходства для тематики (от 0 до 1).",  # noqa: E501
            },
            "status": {
                "type": "string",
                "description": "Статус обработки запроса или сообщение для пользователя.",
            },
        },
        "required": ["has_genre", "has_theme", "genres_scores", "theme_scores", "status"],
    }
    prompt: str = """
    Ты работаешь в рекомендательной системе кинотеатра.
    Твоя задача определить достаточно ли информации предоставил пользователь в описании тематики, которую хочет сегодня посмотреть.
    Анализируй запрос пользователя, чтобы определить, указаны ли жанр фильма (из списка: {genres}) и тематика.
    Если пользователь предоставил запрос из которого косвенно можно понять тематику и жанр, то предугадай их самостоятельно.

    Верни ответ в формате JSON со следующими полями:

    - "genre": строка, выбранный жанр или null, если жанр не указан.
    - "theme": строка, выбранная тематика или null, если тематика не указана.
    - "has_genre": boolean, true, если жанр указан, иначе false.
    - "has_theme": boolean, true, если тематика указана, иначе false.
    - "genres_scores": число, максимальное значение косинусного сходства для жанра (от 0 до 1).
    - "theme_scores": число, максимальное значение косинусного сходства для тематики (от 0 до 1).
    - "status": строка, "OK", если оба поля (has_genre, has_theme) — true.
        Иначе напиши в значение "status" просьбу к пользователю для уточнения его запроса.
        Обращайся к пользователю уважительно и нежно, на "Вы", на русском языке, твоя просьба должна быть не больше 300 символов.

    Ответ должен абсолютно строго соответствовать этой json модели, никаких других атрибутов и слов в ответе не должно быть.

    Для оценки сходства сравни запрос с каждым жанром и тематикой, используя семантическое понимание. Укажи максимальное значение сходства для жанра и тематики (примерно оцени, от 0 до 1).
    Если жанр или тематика не упоминаются явно, установи соответствующее значение has_genre или has_theme в false и score в 0.

    Запрос: "{query}"
    """  # noqa: E501


class Server(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    timeout: int = 30
    backlog: int = 512
    max_requests: int = 1000
    max_requests_jitter: int = 50
    worker_class: str = "uvicorn.workers.UvicornWorker"


class Postgres(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    db: str = "pg_db"

    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"  # noqa: WPS221, E501


class FilmApi(BaseModel):
    host: str = "localhost"
    port: int = 8008
    films_path: str = "/async/api/v1/internal/search-by-vector"
    genre_path: str = "/async/api/v1/internal/genres"

    @property
    def get_film_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.films_path}"

    @property
    def get_genre_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.genre_path}"


class EmbeddingAPI(BaseModel):
    host: str = "localhost"
    port: int = 8007
    path: str = "/embedding-service/api/v1/embedding/fetch-embeddings"

    @property
    def get_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.path}"


class AppConfig(BaseSettings):
    tracing: bool = False
    project_name: str = "nl-consumer"
    docs_url: str = "/nl/openapi"
    openapi_url: str = "/nl/openapi.json"

    server: Server = Server()
    postgres: Postgres = Postgres()
    filmapi: FilmApi = FilmApi()
    llm: LLM = LLM()
    embedding_api: EmbeddingAPI = EmbeddingAPI()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="_",
        extra="ignore",
    )


def _get_config() -> AppConfig:
    log = LoggerSettings()
    log.apply()
    logger = logging.getLogger(__name__)
    app_config = AppConfig()
    logger.info(f"app_config.initialized: {app_config.model_dump_json(indent=4)}")
    return app_config


app_config = _get_config()
