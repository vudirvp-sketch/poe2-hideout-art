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
scripts/              # Утилиты: парсер, измерение footprint'ов
docs/format.md        # Спецификация формата .hideout
исходники/            # Каталог декора от пользователя (7 .hideout + 7 JPG)
  *.hideout           # Каждый файл — небольшая композиция из конкретных декоров
  *.jpg               # Скриншот того же состава в игре (как декор выглядит)
DECO_CATALOG.md       # Каталог декора: что есть, hash, fv-диапазоны, размер
STATUS.md             # Текущее состояние + Known Issues
examples/             # Палитры + тестовые изображения
  palette_canal_warm.json   # 8 декоров от cream до dark
  test_icon_heart.png       # Простая иконка 200×250
  test_portrait.png         # Портрет 400×281 для теста
download/             # Сгенерированные .hideout + preview PNG
  heart.hideout             # 44 placement'а (сердце)
  portrait.hideout          # 53 placement'а (портрет)
tests/                # Тесты библиотеки (341 pass)
```

---

## Быстрый старт

```bash
# Установка
pip install -e .[image,preview]

# Прочитать .hideout
python -m hideout_art inspect исходники/галька.hideout

# Превратить картинку в .hideout (с российской локализацией)
python -m hideout_art img2hideout myphoto.png -o myphoto.hideout \
    --palette examples/palette_canal_warm.json \
    --bounds canal --width 80 --tile-size 12 \
    --bg 255 255 255 --no-alpha \
    --color-metric redmean \
    --language Russian --hideout-hash 60415 \
    --hideout-name "Imported"
```

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
