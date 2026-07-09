# hideout-art

Превращаем картинки в `.hideout`-композиции для **Path of Exile 2**.

Чистый Python. Без внешних сервисов. MIT.

---

## Что это

В PoE2 можно расставлять декоративные объекты на полу убежища вручную.
Если экспортировать убежище в `.hideout`, получится JSON-подобный файл,
где каждый размещённый объект — это одна запись. Меняя эти записи,
можно «рисовать» картинками из декоративных объектов — например,
выложить портрет или сцену.

Проект даёт:

- **Парсер** `.hideout` — корректно обрабатывает duplicate keys (стандартный `json.load` их теряет).
- **Writer** — собирает `.hideout` обратно без потерь.
- **Каталог декора** — `DECO_CATALOG.md` + `src/hideout_art/constants.py`.
  Все хеши взяты из реальных `.hideout` файлов из `исходники/`, не выдуманы.
- **img2hideout** — `src/hideout_art/img2hideout.py`. Берёт PNG/JPG, выбирает
  палитру декораций, расставляет объекты по сетке.
- **CLI** — `python -m hideout_art` для удобного запуска из терминала.

---

## Что в репозитории

```
src/hideout_art/      # Библиотека (парсер, writer, img2hideout, константы, CLI)
scripts/              # Утилиты: парсер, измерение footprint'ов, gen_test_images,
                      # run_img2hideout_test
docs/format.md        # Спецификация формата .hideout
исходники/            # Каталог декора от пользователя (7 .hideout + 7 JPG)
  *.hideout           # Каждый файл — небольшая композиция из конкретных декоров
  *.jpg               # Скриншот того же состава в игре (как декор выглядит)
DECO_CATALOG.md       # Каталог декора: что есть, hash, fv-диапазоны, размер
STATUS.md             # Текущее состояние + Known Issues
examples/             # Палитры + тестовые изображения
  palette_canal_bright.json  # 5 ярких декоров (pink/green/dark) — основная
  palette_canal_warm.json    # 8 тёплых декоров (v0.6.1, не используется)
  test_icon_heart.png        # 200×250 розово-зелёное сердце
  test_portrait.png          # 400×281 портрет
download/             # Сгенерированные .hideout + preview PNG
  heart_v062.hideout         # 686 placement'ов (сердце)
  portrait_v062.hideout      # 873 placement'а (портрет)
tests/                # Тесты библиотеки (341 pass)
```

---

## Быстрый старт

```bash
# Установка
pip install -e .[image,preview]

# Прочитать .hideout
python -m hideout_art inspect исходники/галька.hideout

# Превратить картинку в .hideout (высокая плотность + яркая палитра)
python -m hideout_art img2hideout myphoto.png -o myphoto.hideout \
    --palette examples/palette_canal_bright.json \
    --bounds canal --width 50 \
    --step 1 --scale 2 \
    --origin-x 730 --origin-y 620 \
    --bg 255 255 255 --no-alpha \
    --color-metric redmean \
    --language Russian --hideout-hash 60415 \
    --hideout-name "Imported"
```

**Ключевые параметры для узнаваемости (v0.6.2):**
- `--palette examples/palette_canal_bright.json` — яркие цвета (розовый/зелёный)
- `--step 1 --scale 2` — максимальная плотность (placement каждые 2 wu)
- `--width 40-55` — размер canvas в пикселях (40-55 × aspect ratio)
- `--origin-x/--origin-y` — центрировать в canvas (780, 657 для Canal Hideout)

---

## Как использовать `исходники/`

Это **каталог декора**, а не готовые картины. Каждый файл показывает
несколько декоративных объектов, расставленных в центре убежища, чтобы
увидеть, как они выглядят в игре (JPG рядом — скриншот того же состава).

Что в них искать:

- Какой декор доступен в «Убежище в каналах» (hideout_hash=60415).
- Как выглядит каждый декор (форма, размер, цвет).
- Какие варианты `fv` существуют для каждого декора.
- Минимальное расстояние между placement'ами (для footprint-оценки).

Полный список декора с hash + fv-диапазонами — в `DECO_CATALOG.md`.

---

## Лицензия

MIT. Не аффилирован с Grinding Gear Games. Все названия принадлежат
их владельцам.
