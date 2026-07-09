# STATUS.md

## Текущее состояние

**v0.6.1 — IMG2HIDEOUT FIRST RUN.** Pipeline проверен на двух тестовых
изображениях: простая иконка (сердце 200×250) и реальный портрет
(1229×864 → 400×281). Оба дали валидные `.hideout` файлы с 44 и 53
placement'ами соответственно. Файлы парсятся обратно без потерь,
bbox в пределах Canal Hideout.

**Что изменилось vs v0.6.0:**
- `examples/palette_canal_warm.json` — палитра из 8 декора (от Marble
  Table cream до Camp Gear dark), RGB взяты из DECO_CATALOG.md.
- `examples/test_icon_heart.png` — простая иконка 200×250 (сердце).
- `examples/test_portrait.png` — даунскейл портрета до 400×281.
- `download/heart.hideout` + `download/heart.preview.png` — 44 placement'а.
- `download/portrait.hideout` + `download/portrait.preview.png` — 53 placement'а.
- `src/hideout_art/constants.py`: добавлена `ENGLISH_TO_RUSSIAN` карта
  (27 имён) + `NAME_TRANSLATIONS` + `localize_name()` helper.
- `src/hideout_art/img2hideout.py`: placement names переводятся по
  `language` параметру. При `language="Russian"` — русские имена.
- `src/hideout_art/cli.py`: добавлен `--language` (default English).
- `src/hideout_art/__main__.py`: добавлен, теперь `python -m hideout_art`
  работает как описано в README.
- `src/hideout_art/preview.py`: добавлены цвета для всех 27 art-декоров
  (раньше только 4 оригинальных). Разрешение имени через hash →
  English canonical name → color, чтобы русские имена тоже красились.
- 341 тест pass, 1 skipped.

**Ожидание от пользователя:** импортировать `download/portrait.hideout`
в PoE2, сделать скриншот, прислать. Оценка: узнаваемо или нет?

---

## Known Issues

### KI-12 — RGB marble-декоров не верифицирован
**Симптом**: Pixel-sampling показал тёмные значения (76-110) для
Мраморной скамьи / стен / фонтана, но визуально декор светлый.
Возможно, sampling попал в тень под объектом.
**Фикс**: ручной скриншот каждого marble-декора на светлом фоне.
**Не блокирует**: img2hideout (используются тёплые тона, не marble).

### KI-13 — Footprint для single-observation декоров
**Симптом**: 7 декоров имеют только 1 placement в `исходники/`,
поэтому их footprint не измерен. Это: Falling Sand, Fringe Moss,
Maraket Treasures, Petrified Cave Figure, Cave Coral, Marble
Bench/Walls/Fountain, Camp Gear, Marble Table (2 obs).
**Фикс**: пользователь делает новый `.hideout` с 2+ placement'ами
каждого такого декора, отправляет.
**Не блокирует**: img2hideout (используем DEFAULT_TILE_SIZE=23).

### KI-14 — Вращение декора не верифицировано визуально
**Симптом**: Декор **можно** вращать (`r` поле), но неизвестно, как
конкретные декоры выглядят при вращении.
**Фикс**: пользователь делает тест — 1 декор с разными r (0, 16384,
32768, 49152) → скриншот → понимаем визуальный эффект.
**Не блокирует**: img2hideout v1 (по умолчанию r=0).

### KI-15 — Img2hideout recognizability не подтверждена
**Симптом**: Pipeline работает (44-53 placement'а, валидный .hideout),
но узнаваемость картинки в PoE2 не подтверждена пользователем.
**Фикс**: пользователь импортирует `download/portrait.hideout` →
скриншот → оценка "узнаваемо или нет".
**Не блокирует**: ничего — ждём ответа пользователя.

---

## TODO — приоритеты

1. **Получить скриншот от пользователя** — импорт `download/portrait.hideout`
   в PoE2 → скриншот → оценка узнаваемости.

2. **Если картинка не читается** → расширить палитру декора: попросить
   у пользователя ещё `.hideout` файлы с декором, которого нет в
   текущем каталоге (например, синие/зелёные/яркие декоры).

3. **Если читается** → добавить multi-pass (outline + fill) в
   img2hideout: сначала выложить контур одним декором, потом fill
   другим.

4. **Marble RGB fix (KI-12)** — после ручных скриншотов.

5. **Footprint measurement (KI-13)** — после новых `.hideout` от
   пользователя.

---

## Что НЕ сделано (намеренно)

- Multi-pass img2hideout — отложен до подтверждения single-pass
  узнаваемости.
- Расширение палитры — отложено до подтверждения, что текущих 27
  декоров недостаточно.
- Никаких новых `.hideout` файлов сверх двух тестовых не сгенерировано.

---

## Файловая структура проекта (v0.6.1)

```
README.md                # Что за проект
DECO_CATALOG.md          # Каталог декора (27 объектов + 18 functional)
STATUS.md                # Этот файл
worklog.md               # Журнал работы (append-only)
docs/format.md           # Спецификация .hideout формата
docs/screenshots/        # In-game скриншоты (2 файла)
src/hideout_art/         # Библиотека: parser/writer/img2hideout/constants/cli/...
  __main__.py            # NEW: позволяет python -m hideout_art
scripts/                 # parse_hideout.py, measure_decorations.py
tests/                   # Тесты библиотеки (341 pass)
examples/                # Палитры + тестовые изображения (NEW)
  palette_canal_warm.json
  test_icon_heart.png
  test_portrait.png
  README.md
исходники/               # Каталог декора от пользователя (7 .hideout + 7 JPG)
download/                # NEW: сгенерированные .hideout + preview
  heart.hideout
  heart.preview.png
  portrait.hideout
  portrait.preview.png
  img2hideout_report.txt
```

---

## Как воспроизвести download/

```bash
# Установка
pip install -e .[image,preview]

# Генерация тестовых изображений
python /home/z/my-project/scripts/gen_test_images.py

# Прогон img2hideout на обоих изображениях
python /home/z/my-project/scripts/run_img2hideout_test.py

# Или вручную через CLI:
python -m hideout_art img2hideout examples/test_portrait.png \
    -o download/portrait.hideout \
    --palette examples/palette_canal_warm.json \
    --bounds canal --width 80 --tile-size 12 \
    --bg 255 255 255 --no-alpha \
    --color-metric redmean \
    --language Russian --hideout-hash 60415 \
    --hideout-name "Imported"
```
