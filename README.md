

### Базовый отчет по среднему времени ответа

```bash
python3 main.py --file example.log --report average
```

### Обработка нескольких файлов

```bash
python main.py --file log1.log --file log2.log --file log3.log --report average
```

### Фильтрация по дате

```bash
python3 main.py --file example.log --report average --date 2025-06-22
```




## Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием кода
python3 -m pytest test_main.py --cov=main --cov-report=term-missing

```

Текущее покрытие кода: ~95%

