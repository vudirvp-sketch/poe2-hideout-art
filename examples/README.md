# Examples

Папка для примеров палитр и тестовых изображений. Сейчас пусто —
будет наполняться по мере тестирования `img2hideout`.

## Планируется

- `palette_default.json` — палитра по умолчанию, основанная на
  `DECO_CATALOG.md`. Каждый декор → его RGB.
- `palette_warm.json` — тёплая палитра (камни/песок/дерево).
- `palette_cool.json` — холодная палитра (мрамор/водоросли).
- `test_photo.png` — простое изображение для первого теста.

## Как создать свою палитру

1. Открой `DECO_CATALOG.md`, выбери декоры под свою задачу.
2. Для каждого декора возьми RGB из колонки «Цвет (RGB)».
3. Создай JSON-файл в формате:

```json
{
  "entries": [
    {"color": [127, 111, 86],  "decoration": "Coastal Pebble", "weight": 1.0},
    {"color": [125, 112, 87],  "decoration": "Maraket Rubble", "weight": 1.0},
    {"color": [159, 136, 109], "decoration": "Cave Fossil",    "weight": 1.0}
  ]
}
```

4. Запусти:

```bash
hideout-art img2hideout mypicture.png -o mypicture.hideout \
    --palette examples/my_palette.json \
    --bounds canal --width 80
```
