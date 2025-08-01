class Mapping:
    _settings = {
        "index": {
            "routing": {
                "allocation": {"include": {"_tier_preference": "data_content"}},
            },
            "refresh_interval": "1s",
            "number_of_shards": "1",
            "number_of_replicas": "1",
            "analysis": {
                "filter": {
                    "russian_stemmer": {"type": "stemmer", "language": "russian"},
                    "english_stemmer": {"type": "stemmer", "language": "english"},
                    "english_possessive_stemmer": {
                        "type": "stemmer",
                        "language": "possessive_english",
                    },
                    "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                    "english_stop": {"type": "stop", "stopwords": "_english_"},
                },
                "analyzer": {
                    "ru_en": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stop",
                            "english_stemmer",
                            "english_possessive_stemmer",
                            "russian_stop",
                            "russian_stemmer",
                        ],
                    },
                },
            },
        },
    }
    films = {
        "settings": _settings,
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "actors": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "ru_en"},
                    },
                },
                "actors_names": {"type": "text", "analyzer": "ru_en"},
                "description": {"type": "text", "analyzer": "ru_en"},
                "directors": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "ru_en"},
                    },
                },
                "directors_names": {"type": "text", "analyzer": "ru_en"},
                "genres": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "ru_en"},
                    },
                },
                "genres_names": {"type": "text", "analyzer": "ru_en"},
                "id": {"type": "keyword"},
                "imdb_rating": {"type": "float"},
                "title": {
                    "type": "text",
                    "fields": {"raw": {"type": "keyword"}},
                    "analyzer": "ru_en",
                },
                "type": {"type": "keyword"},
                "writers": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "ru_en"},
                    },
                },
                "writers_names": {"type": "text", "analyzer": "ru_en"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine",
                    "index_options": {"type": "hnsw", "m": 32, "ef_construction": 150},
                },
            },
        },
    }
    genres = {
        "settings": _settings,
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "name": {"type": "text", "analyzer": "ru_en"},
            },
        },
    }
    persons = {
        "settings": _settings,
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "name": {"type": "text", "analyzer": "ru_en"},
            },
        },
    }
