#### Аналитическое сравнение производительности ClickHouse и Vertica для сервиса метрик

Цель данного материала - сравнить производительность операций вставки и выборки данных в колоночных СУБД ClickHouse и Vertica на идентичном объеме данных (5 000 000 записей) и определить оптимальное решение для сервиса метрик.

##### 1. Введение
Сервис метрик (metrics) обрабатывает большие объемы событий с временными метками (timestamp) и идентификаторами пользователей (user_uuid). Требования к системе хранения:

- Высокая скорость вставки потоковых данных.

- Эффективное выполнение аналитических запросов (агрегации, фильтрации по времени, сортировка).

- Оперативное получение данных для построения отчетов и дашбордов.

Колоночные СУБД ClickHouse и Vertica являются ключевыми кандидатами для решения этой задачи. В данном докладе представлены результаты сравнительного тестирования производительности операций вставки и типичных запросов.

##### 2. Методология тестирования
Объем тестовых данных составлял 5 000 000 записей. Вставка данных выполнялась с использованием 5 параллельных процессов для обеих СУБД. Тестировались различные размеры батчей при вставке (1000, 5000, 10000 записей за один запрос). Тесты проводились на идентичной конфигурации сервера.

Для наполнения данных использовались следущие скрипты `docs/comparison_column_db/clickhouse.py` и `docs/comparison_column_db/vertica.py`. Тестовые запросы проводились с использование СУБД `DBeaver`.

Тестовые запросы:

- `SELECT * FROM test t ORDER BY t."timestamp" LIMIT 3 OFFSET 3500000;`
(Сортировка + Пагинация с большим offset)

- `SELECT SUM(value) FROM test t;`
(Простая агрегация)

- `SELECT AVG(value) FROM test t;`
(Простая агрегация)

- `SELECT * FROM test t WHERE t.timestamp > '2025-05-29 18:28:10' ORDER BY t.user_uuid, t.timestamp ASC LIMIT 3;`
(Фильтрация по времени + Сортировка по двум полям + Лимит)

##### 3. Результаты тестирования

###### Скорость вставки данных (5 000 000 записей, 5 процессов)

| Размер батча | ClickHouse (сек) | Vertica (сек) | Отношение Vertica/ClickHouse |
| ------- | -------- | ------- | -------- |
| 1000 | 71.60 | 167.92 | 2.34x |
| 5000 | 66.60 | 117.96 | 	1.77x |
| 10000 | 68.00 | 119.31 | 1.75x |

Выводы по вставке:

- ClickHouse демонстрирует значительно более высокую скорость вставки при всех размерах батчей.

- Наилучшая производительность ClickHouse наблюдается при размере батча 5 000 записей (66.6 сек).

- Vertica показывает существенно более медленную скорость вставки, особенно при малых размерах батчей (в 2.34 раза медленнее при батче 1000). Оптимальный размер батча для Vertica в этом тесте - 5000-10000 (117-119 сек), но даже он на ~75% медленнее, чем оптимальный результат ClickHouse.

- ClickHouse менее чувствителен к выбору размера батча в диапазоне 1000-10000 записей по сравнению с Vertica.

###### Скорость выполнения запросов

| Запрос | ClickHouse (сек) | Vertica (сек) | Отношение Vertica/ClickHouse |
| ------- | -------- | ------- | -------- |
| `SELECT * FROM test t ORDER BY t."timestamp" LIMIT 3 OFFSET 3500000`  | 0.6 | 1.6 | 2.67x |
| `SELECT SUM(value) FROM test t`  | 0.014 | 0.027 | 1.93x |
| `SELECT AVG(value) FROM test t;`  | 0.011 | 0.020 | 2.27x |
| `SELECT * FROM test t WHERE t.timestamp > '2025-05-29 18:28:10' ORDER BY t.user_uuid, t.timestamp ASC LIMIT 3;`   | 0.049 | 1.6 | 32.65x |

Выводы по запросам:

- ClickHouse абсолютно доминирует в запросе, требующих сортировки больших объемов данных запрос 4. Разница в производительности составляет более 2.67 раз для пагинации с большим offset и более 32 раза для запроса с фильтрацией по времени и сортировкой по двум полям. Это критично для задач аналитики временных рядов и поиска конкретных записей.

- В простых агрегациях (SUM, AVG) ClickHouse также показывает себя быстрее, опережая Vertica примерно в 2 раза.

- Vertica показывает приемлемую, но не лидирующую, скорость на простых агрегациях.

##### 4. Результаты тестирования

На основании проведенного тестирования производительности операций вставки данных и выполнения типичных аналитических запросов на идентичном наборе данных (5 млн записей) можно сделать следующие заключения:

1. ClickHouse показал абсолютное превосходство в скорости вставки данных, будучи в 1.75 - 2.34 раза быстрее Vertica в зависимости от размера батча. Это критически важно для сервиса метрик, обрабатывающего высокоскоростные потоки событий.

2. ClickHouse продемонстрировал выдающуюся производительность на запросах, характерных для аналитики временных рядов и работы с большими данными:
- Запросы с сортировкой и пагинацией (особенно с большим OFFSET) выполняются на порядок быстрее (в 2.5+ раз).
- Запросы с фильтрацией по времени и сложной сортировкой выполняются крайне эффективно (в 32+ раза быстрее).

3. В простых агрегациях (SUM, AVG) ClickHouse также имеет стабильное преимущество примерно в 2 раза.

4. Vertica, несмотря на свою репутацию мощной аналитической СУБД, в данном конкретном сценарии (вставка потоковых данных + аналитические запросы, характерные для метрик) значительно уступает ClickHouse по всем измеренным показателям производительности.

Исходя из полученных результатов, ClickHouse является более оптимальным выбором колоночной СУБД для сервиса метрик (metrics).
