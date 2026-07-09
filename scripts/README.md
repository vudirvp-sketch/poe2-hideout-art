# Scripts

Утилиты для разработки и анализа. Не входят в основную библиотеку
`src/hideout_art/`. Скрипты могут зависеть от `matplotlib`, `pillow` —
они не объявлены в `pyproject.toml`.

## Доступные скрипты

| Файл | Назначение |
|---|---|
| `parse_hideout.py` | CLI-обёртка над парсером. Показывает статистику по `.hideout`: счёт placements, top-doodad'ы, bbox. |
| `measure_decorations.py` | Измеряет footprint каждого декора из `исходники/*.hideout` (минимальное расстояние между placement'ами одного типа). Результаты складываются в `decoration_footprints.json` (gitignored). |
| `gen_test_images.py` | Генерирует `examples/test_icon_heart.png` (200×250) и `examples/test_portrait.png` (400×281 даунскейл загруженного портрета). Запуск: `python scripts/gen_test_images.py`. |
| `run_img2hideout_test.py` | Прогоняет `img2hideout` на обоих тестовых изображениях, пишет `.hideout` + preview в `download/`. Запуск: `python scripts/run_img2hideout_test.py`. |

## Запуск

```bash
# Инспекция .hideout файла
python scripts/parse_hideout.py исходники/галька.hideout

# Измерение footprint'ов всех декоров
python scripts/measure_decorations.py

# Сгенерировать тестовые изображения (нужна Pillow)
python scripts/gen_test_images.py

# Прогнать img2hideout на тестовых изображениях (нужна Pillow + matplotlib)
python scripts/run_img2hideout_test.py
```

## Что gitignored

`*.json` и `*.png` в этой директории (результаты запусков) — локально
для отладки, не коммитятся.
