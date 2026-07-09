# STATUS.md

## Текущее состояние

**v0.6.2 — HIGH DENSITY + BRIGHT PALETTE.** Pipeline переписан после
фидбека пользователя: "каша получилась и ничего не узнаваемо, используй
более мелкие декораторы в качестве точек и линий!"

Пользователь прислал референс (скриншот 234156.jpg) — СЕРДЦЕ из
розового "Плавающего песка" сверху + зелёной "Высокой травы" снизу,
расставленных **очень плотно** (сплошное пятно, без разрывов).

**Что изменилось vs v0.6.1:**
- **Палитра**: `palette_canal_bright.json` вместо `palette_canal_warm.json`.
  Яркие цвета: Falling Sand (розовый) + Long Grass (зелёный) + Fringe Moss
  (светло-зелёный) + Sand Tussock (тёмный) + Camp Gear (very dark).
- **RGB fix (KI-16)**: Falling Sand = розовый (255,192,203), Long Grass =
  зелёный (46,125,50). Pixel-sampling 0.2.6 был неверным (попал в тени/
  промежутки между частицами). VLM 0.2.5 был прав всё время. Подтверждено
  скриншотом 234156.jpg.
- **Плотность**: `step=1, scale=2` (placement каждые 2 wu) вместо
  `tile_size=12` (каждые 12 wu). 4-6× больше placement'ов → сплошное
  пятно как на референсе.
- **Центрирование**: origin вычисляется так, чтобы центр изображения
  попадал в центр canvas (780, 657). Раньше изображение было в углу.
- **Zoom preview**: новый `*.preview_zoom.png` — превью с зумом на bbox
  размещений, чтобы форма была видна (раньше превью показывало весь
  canvas и сердце было крошечным).
- **Heart input**: обновлён — розовый верх + зелёный низ (м匹配ает
  референс 234156.jpg), вместо чёрного силуэта.
- `Fringe Moss` добавлен в `ENGLISH_TO_RUSSIAN` карту ("Мох с опушки").
- 341 тест pass, 1 skipped.

**Результат (VLM-верифицировано):**
- `heart_v062.hideout` (686 placement'ов): VLM подтвердил "форма сердца,
  узнаваема, розовый+зелёный".
- `portrait_v062.hideout` (873 placement'а): VLM подтвердил "форма
  человеческого лица/портрета, узнаваема".

**Ожидание от пользователя:** импортировать `download/heart_v062.hideout`
и `download/portrait_v062.hideout` в PoE2 → скриншоты → оценка
узнаваемости в игре (не в превью).

---

## Known Issues

### KI-12 — RGB marble-декоров не верифицирован
**Симптом**: Pixel-sampling показал тёмные значения (76-110) для
Мраморной скамьи / стен / фонтана, но визуально декор светлый.
**Фикс**: ручной скриншот каждого marble-декора на светлом фоне.
**Не блокирует**: img2hideout (используются яркие тона, не marble).

### KI-13 — Footprint для single-observation декоров
**Симптом**: 7 декоров имеют только 1 placement в `исходники/`.
**Фикс**: пользователь делает новый `.hideout` с 2+ placement'ами.
**Не блокирует**: img2hideout (step=1, scale=2 — не зависит от footprint).

### KI-14 — Вращение декора не верифицировано визуально
**Симптом**: Декор **можно** вращать (`r` поле), но неизвестно, как
конкретные декоры выглядят при вращении.
**Фикс**: пользователь делает тест — 1 декор с разными r.
**Не блокирует**: img2hideout (по умолчанию r=0).

### KI-15 — Img2hideout in-game recognizability не подтверждена
**Симптом**: Pipeline работает, VLM подтверждает узнаваемость в
**превью**, но узнаваемость в **самой игре** не подтверждена.
**Фикс**: пользователь импортирует `download/heart_v062.hideout` и
`download/portrait_v062.hideout` → скриншоты → оценка.
**Не блокирует**: ничего — ждём ответа.

### KI-16 (RESOLVED) — RGB Falling Sand / Long Grass были неверными
**Closed в v0.6.2**: Pixel-sampling 0.2.6 дал тёмные значения
(145,125,101 brown для Falling Sand; 136,119,93 brown-tan для Long
Grass), но VLM 0.2.5 был прав: Falling Sand = розовый (255,192,203),
Long Grass = зелёный (46,125,50). Подтверждено скриншотом 234156.jpg.
Причина ошибки: sampling попал в тени под объектом / промежутки между
частицами Falling Sand. **Решение**: использовать VLM-значения для
этих двух декоров; pixel-sampling оставлен в комментариях для истории.

### KI-17 — Fringe Moss hash не верифицирован в исходниках
**Симптом**: Fringe Moss (hash=1459723677) имеет 0 placements в
`исходники/`, но пользователь использует его на скриншоте 234156.jpg
("Мох с опушки"). Hash взят из ранних версий каталога, не подтверждён
реальным .hideout файлом.
**Фикс**: пользователь присылает `.hideout` файл, где Fringe Moss
размещён, → верифицируем hash.
**Не блокирует**: img2hideout работает (если hash неверный, декор
просто не появится в игре, файл не сломается).

---

## TODO — приоритеты

1. **Получить скриншоты от пользователя (KI-15)** — импорт
   `download/heart_v062.hideout` и `download/portrait_v062.hideout`
   в PoE2 → скриншоты → оценка узнаваемости в игре.

2. **Если узнаваемо** → добавить multi-pass (outline + fill) в
   img2hideout: контур одним декором, fill другим, highlights третьим.

3. **Если не узнаваемо** → расширить палитру: попросить у пользователя
   `.hideout` файлы с декором, которого нет в каталоге (синие/жёлтые/
   яркие). Особенно — верифицировать Fringe Moss hash (KI-17).

4. **Marble RGB fix (KI-12)** — после ручных скриншотов.

5. **Footprint measurement (KI-13)** — после новых `.hideout` от
   пользователя.

---

## Что НЕ сделано (намеренно)

- Multi-pass img2hideout — отложен до подтверждения single-pass
  узнаваемости в игре (не в превью).
- Расширение палитры — отложено до подтверждения, что текущих 5
  ярких декоров недостаточно.
- Верификация Fringe Moss hash (KI-17) — нужен `.hideout` от пользователя.

---

## Файловая структура проекта (v0.6.2)

```
README.md                # Что за проект
DECO_CATALOG.md          # Каталог декора (27 объектов + 18 functional)
STATUS.md                # Этот файл
worklog.md               # Журнал работы (append-only)
docs/format.md           # Спецификация .hideout формата
docs/screenshots/        # In-game скриншоты (2 файла)
src/hideout_art/         # Библиотека
  __main__.py            # python -m hideout_art
scripts/                 # parse_hideout, measure_decorations, gen_test_images,
                         # run_img2hideout_test
tests/                   # 341 pass, 1 skipped
examples/                # Палитры + тестовые изображения
  palette_canal_warm.json     # 8 тёплых декоров (v0.6.1, не используется)
  palette_canal_bright.json   # 5 ярких декоров (v0.6.2, основная)
  test_icon_heart.png         # 200×250 розово-зелёное сердце
  test_portrait.png           # 400×281 портрет
исходники/               # Каталог декора от пользователя (7 .hideout + 7 JPG)
download/                # Сгенерированные .hideout + preview
  heart_v062.hideout           # 686 placement'ов (сердце)
  heart_v062.preview.png       # full canvas
  heart_v062.preview_zoom.png  # zoom на bbox
  portrait_v062.hideout        # 873 placement'а (портрет)
  portrait_v062.preview.png
  portrait_v062.preview_zoom.png
  img2hideout_report_v062.txt
```

---

## Как воспроизвести download/

```bash
# Установка
pip install -e .[image,preview]

# Генерация тестовых изображений
python scripts/gen_test_images.py

# Прогон img2hideout на обоих изображениях (v0.6.2: high density + bright palette)
python scripts/run_img2hideout_test.py

# Или вручную через CLI:
python -m hideout_art img2hideout examples/test_icon_heart.png \
    -o download/heart.hideout \
    --palette examples/palette_canal_bright.json \
    --bounds canal --width 40 \
    --step 1 --scale 2 \
    --origin-x 740 --origin-y 607 \
    --bg 255 255 255 --no-alpha \
    --color-metric redmean \
    --language Russian --hideout-hash 60415 \
    --hideout-name "Imported"
```
