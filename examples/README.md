# Examples

Палитры и тестовые изображения для `img2hideout`.

## Палитры

### `palette_canal_bright.json` — ОСНОВНАЯ (v0.6.2)

5 ярких декоров для узнаваемых рисунков. RGB значения подтверждены
скриншотом пользователя 234156.jpg (см. KI-16 в STATUS.md).

| Декор (English) | Russian | RGB | Назначение |
|---|---|---|---|
| Falling Sand | Летающий песок | (255,192,203) pink | розовые/светлые участки |
| Long Grass | Высокая трава | (46,125,50) green | зелёные участки |
| Fringe Moss | Мох с опушки | (139,195,74) light green | светло-зелёные блики |
| Sand Tussock | Песчаный кустарник | (112,99,79) dark olive-tan | тёмные mid тона |
| Camp Gear | Снаряжение из лагеря | (70,66,56) very dark | самые тёмные участки |

**Важно:** RGB для Falling Sand и Long Grass — VISUAL (VLM-оценки),
не pixel-sampled. Pixel-sampling 0.2.6 дал тёмные значения, потому что
попал в тени/промежутки между частицами. VLM был прав — подтверждено
скриншотом 234156.jpg. См. KI-16 в STATUS.md.

### `palette_canal_warm.json` — устаревшая (v0.6.1)

8 тёплых brown/tan декоров. **Не используется** — давала "кашу"
(неправильные цвета для портрета/сердца). Оставлена для истории.

## Тестовые изображения

### `test_icon_heart.png`

200×250 px: розовое сердце сверху + зелёное снизу, на белом фоне.
Сгенерирована скриптом `scripts/gen_test_images.py`. М匹配ает референс
пользователя (скриншот 234156.jpg).

При `target_width=40, step=1, scale=2` → 686 placement'ов, сердце
узнаваемо в превью (VLM-подтверждено).

### `test_portrait.png`

400×281 px (даунскейл с 1229×864). Портрет мужчины с бородой.

При `target_width=55, step=1, scale=2` → 873 placement'а, портрет
узнаваем в превью (VLM-подтверждено).

## Как использовать

```bash
# Сгенерировать .hideout из портрета (v0.6.2 — высокая плотность)
python -m hideout_art img2hideout examples/test_portrait.png \
    -o download/portrait.hideout \
    --palette examples/palette_canal_bright.json \
    --bounds canal --width 55 \
    --step 1 --scale 2 \
    --origin-x 725 --origin-y 619 \
    --bg 255 255 255 --no-alpha \
    --color-metric redmean \
    --language Russian --hideout-hash 60415 \
    --hideout-name "Imported"
```

**Ключевые параметры для узнаваемости:**
- `--palette examples/palette_canal_bright.json` — яркие цвета
- `--step 1 --scale 2` — максимальная плотность (placement каждые 2 wu)
- `--width 40-55` — размер canvas в пикселях
- `--origin-x/--origin-y` — центрировать в canvas (центр Canal Hideout = 780, 657)

## Как создать свою палитру

1. Открой `DECO_CATALOG.md`, выбери декоры под свою задачу.
2. Для каждого декора возьми RGB из колонки «Цвет (RGB)».
   **Важно:** для Falling Sand / Long Grass используй VISUAL значения
   (розовый/зелёный), не PIXEL (тёмные) — см. KI-16.
3. Создай JSON-файл в формате:

```json
{
  "entries": [
    {"color": [255, 192, 203], "decoration": "Falling Sand", "weight": 1.0},
    {"color": [46, 125, 50],   "decoration": "Long Grass",   "weight": 1.0}
  ]
}
```

4. Запусти `img2hideout` с `--palette` флагом (см. пример выше).

**Важно:** `decoration` поле использует **английские** canonical имена
из `KNOWN_HASHES` (`src/hideout_art/constants.py`). При `--language Russian`
имена переводятся в русском `.hideout` файле автоматически.
