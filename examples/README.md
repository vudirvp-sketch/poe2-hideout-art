# Examples

Палитры и тестовые изображения для `img2hideout`.

## Палитры

### `palette_canal_warm.json`

8 декоров из `DECO_CATALOG.md`, охватывают тёплый диапазон от cream до
dark. Подходит для портретов / силуэтов на белом фоне. RGB значения —
pixel-sampled из реальных `.hideout` файлов.

| Декор (English) | RGB | Назначение |
|---|---|---|
| Marble Table | (196,170,136) | cream — светлые участки |
| Cave Coral | (170,144,114) | light brown — мягкие блики |
| Cave Fossil | (159,136,109) | warm brown — средние тона |
| Coastal Pebble | (127,111,86) | tan — нейтральный mid |
| Maraket Rubble | (125,112,87) | brown — нейтральный mid |
| Sand Tussock | (112,99,79) | olive-tan — тёмные mid |
| Small Coastal Stone | (81,80,60) | dark gray — тёмные тона |
| Camp Gear | (70,66,56) | very dark — самые тёмные участки |

## Тестовые изображения

### `test_icon_heart.png`

Простая иконка 200×250 px: чёрное сердце на белом фоне. Сгенерирована
скриптом `scripts/gen_test_images.py`. Sanity check — pipeline должен
выдать ~40-50 placement'ов, формирующих силуэт сердца.

### `test_portrait.png`

Портрет 400×281 px (даунскейл с 1229×864). Реальный тест на
узнаваемость: pipeline должен выложить силуэт человека ~50-60
placement'ами.

## Как использовать

```bash
# Сгенерировать .hideout из портрета
python -m hideout_art img2hideout examples/test_portrait.png \
    -o download/portrait.hideout \
    --palette examples/palette_canal_warm.json \
    --bounds canal --width 80 --tile-size 12 \
    --bg 255 255 255 --no-alpha \
    --color-metric redmean \
    --language Russian --hideout-hash 60415 \
    --hideout-name "Imported"
```

## Как создать свою палитру

1. Открой `DECO_CATALOG.md`, выбери декоры под свою задачу.
2. Для каждого декора возьми RGB из колонки «Цвет (RGB)».
3. Создай JSON-файл в формате:

```json
{
  "entries": [
    {"color": [127, 111, 86],  "decoration": "Coastal Pebble", "weight": 1.0},
    {"color": [125, 112, 87],  "decoration": "Maraket Rubble", "weight": 1.0}
  ]
}
```

4. Запусти `img2hideout` с `--palette` флагом (см. пример выше).

**Важно:** `decoration` поле использует **английские** canonical имена
из `KNOWN_HASHES` (`src/hideout_art/constants.py`). При `--language Russian`
имена переводятся в русском `.hideout` файле автоматически.
