# Scripts

Утилиты для разработки и анализа. Не входят в основную библиотеку
`src/hideout_art/`. Скрипты могут зависеть от `matplotlib`, `pillow` —
они не объявлены в `pyproject.toml`.

## Доступные скрипты

| Файл | Назначение |
|---|---|
| `parse_hideout.py` | CLI-обёртка над парсером. Показывает статистику по `.hideout`: счёт placements, top-doodad'ы, bbox. |
| `measure_decorations.py` | Измеряет footprint каждого декора из `исходники/*.hideout` (минимальное расстояние между placement'ами одного типа). Результаты складываются в `decoration_footprints.json` (gitignored). |

## Запуск

```bash
# Инспекция .hideout файла
python scripts/parse_hideout.py исходники/галька.hideout

# Измерение footprint'ов всех декоров
python scripts/measure_decorations.py
```

## Что gitignored

`*.json` и `*.png` в этой директории (результаты запусков) — локально
для отладки, не коммитятся.
