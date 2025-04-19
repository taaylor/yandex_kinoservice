pip install poetry  # установка
poetry config virtualenvs.in-project true  # в конфиге poetry виртуалка poetry была в корневой директории
poetry self add poetry-plugin-shell  # установка расширения poetry- shell (для активации venv)
poetry shell  # активация venv (строго в корневой директории)
poetry install  # установка зависимостей
pre-commit install  # установка хука чтобы он сраюатывал перед коммитом
pre-commit run --all-files  # запуск линтера (прекоммита) - проверка

pre-commit clean  # чистит кеш (правила проверки кода)

удаляет все папки __pycache__/ в директории src, чтобы не раздражали :) : `find . -type d -name "__pycache__" -exec rm -r {} +`

## Выгрузка данных с Elasticsearch

`curl -X GET "http://localhost:9200/_mapping?pretty" > elastisearch_dump/index_mappings.json` - делает дамп всех индексов

`curl -X GET "http://localhost:9200/_search?size=10000&pretty=true" > elastisearch_dump/all_data.json` - делает дамп всех данных
Размер size=10000 — это лимит на одну выборку.

`curl -X PUT "http://localhost:9200/_bulk" -H "Content-Type: application/json" --data-binary "@all_data.json"` - восстановление данных


вместо parse_raw() рекомендуемо использовать model_validate_json() для преобразования json в pydantic объект


| pip                                       | poetry |
|-------------------------------------------|--------|
| `pip install -r requirements.txt`        | `poetry install` |
| `pip install some_library`               | `poetry add some_library` |
| `pip install -e .`                        | `poetry add --editable .` |
| `pip freeze`                              | `poetry export --without-hashes --format=requirements.txt` |
| `pip freeze > requirements.txt`          | `poetry export --without-hashes --format=requirements.txt --output requirements.txt` |
| `pip list`                                | `poetry show` |
| `pip uninstall some_library`             | `poetry remove some_library` |
| `pip check` (проверка зависимостей)      | `poetry check` |
| (редактирование requirements.txt вручную) | (редактировать `pyproject.toml` вручную и запустить `poetry update`) |
* Если нужна более подробная информация, можно добавить --tree к poetry show, чтобы увидеть зависимости в виде дерева.
