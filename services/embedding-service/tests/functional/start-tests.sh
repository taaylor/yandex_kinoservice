#!/bin/sh

echo "Запуск waiters..."
python3 ./tests/functional/utils/wait_for_api.py

echo "Запуск тестов..."

pytest ./tests/functional/src -v -rP
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "Обнаружены провалившиеся тесты. Повторный запуск через 5 сек..."
    sleep 5
    pytest ./tests/functional/src -v --last-failed -rP
    FINAL_EXIT_CODE=$?
    if [ $FINAL_EXIT_CODE -ne 0 ]; then
        echo "Повторный запуск тестов провалился!"
        exit $FINAL_EXIT_CODE
    else
        echo "Повторный запуск тестов прошел успешно!"
    fi
else
    echo "Все тесты пройдены успешно!"
fi
