from pydantic import BaseModel


class Postgres(BaseModel):
    host: str = "postgres"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    db: str = "pg_db"

    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

class MongoDB(BaseModel):
    host: str = "mongodb_router"
    port: int = 27017
    name: str = "kinoservice"
    like_coll: str = "likeCollection"
    bookmark_coll: str = "bookmarkCollection"
    reviews_coll: str = "reviewsCollection"

    @property
    def ASYNC_DATABASE_URL(self):
        return f"mongodb://{self.host}:{self.port}"

app_config = Postgres()
