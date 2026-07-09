# STATUS.md

Текущее состояние проекта `poe2-hideout-art`. Короткая живая памятка для
агента/человека: что работает, что сломано, что делать дальше. Длинную
историю изменений не ведём — для этого есть `CHANGELOG.md`.

## Что работает (проверено 2026-07-09, версия 0.2.6)

- Парсер `.hideout` (толерантный, регэксп, сохраняет дубликаты ключей).
- Врайтер (байт-совместимый, дубликаты ключей сохраняет).
- Геометрические трансформации: `shift`, `rotate`, `mirror_x`, `mirror_y`,
  `recombine`.
- Превью в PNG (matplotlib, по одной точке на размещение).
- Конвейер `img2hideout`:
  - базовый режим совместим с 0.1.0 побайтово;
  - alpha-канал PNG, 3 цветовых метрики, Floyd-Steinberg dithering;
  - jitter, `step`/`tile_size`, `bounds` (включая `--bounds canal`),
  - `resample`, `--preview` в CLI.
- CLI: `inspect`, `layers`, `stats`, `preview`, `shift`, `transfer`,
  `img2hideout`.
- Каталог хешей: **47 известных декораций** (11 функциональных + 8 NPC +
  4 исходных art + 5 Maraket/Coastal Pebble + 18 Canal из «исходники/» +
  1 Seaweed добавлена в 0.2.5).
- Геометрия Canal Hideout: `CANAL_HIDEOUT_HASH = 60415`,
  `CANAL_HIDEOUT_BOUNDS = (700, 540, 860, 775)`.
- **Каталог размеров декораций (0.2.3, обновлён 0.2.5):**
  `DECORATION_FOOTPRINT_CATALOG` покрывает все 28 art-декораций.
- **Pixel sampling скрипт (0.2.6, НОВОЕ):** `scripts/sample_pixels.py`
  берёт `.hideout` + соответствующий `.jpg` и семплит реальные пиксели
  под каждым размещением. Закрывает KI-11. Поддерживает:
  - Auto-calibration: `--world-bbox canal` (по умолчанию) или
    `--world-bbox functional` (расширяет bbox до всех функциональных
    объектов — рекомендуется, т.к. Stash/Ange/Reforging Bench лежат
    вне Canal canvas).
  - Manual calibration: `--calibration anchors.json` с ≥2 anchor
    соответствиями (world → pixel), least-squares affine fit.
  - Diagnostic overlay PNG: `--diagnostic` — placement dots на скриншоте
    для визуальной проверки калибровки.
  - Все 7 скриншотов из `исходники/` отсемплены → `scripts/sampled_all.json`.
  - Sanity-check: Stash даёт believable brown wood (R>G>B, 64-182) во
    всех 7 скриншотах → калибровка валидна.
- **Pixel-sampled RGB (0.2.6, НОВОЕ):** ground-truth median RGB для 25
  из 28 art-декораций (Cordilina, Fringe Moss, Petrified Cave Figure
  не имеют placements в исходниках). Значения систематически отличаются
  от VLM-оценок на 30-100+ RGB точек — см. таблицу сравнения в
  `examples/palette_2b.json` → `_pixel_sampling_summary_0_2_6`.
- Тесты: см. `CHANGELOG.md` за актуальным счётчиком.

## Известные проблемы (Known Issues)

Все ранее задокументированные KI-1..KI-10 закрыты. Активные:

| KI  | Статус      | Что                                                |
|-----|-------------|----------------------------------------------------|
| KI-2 | partial 0.2.6 | 5/6 TODO закрыты. Остался `skin` — Sand Tussock подтверждён pixel-sampling как тёмный olive-tan (112,99,79), НЕ skin tone. Нужна новая peach/tan декорация. |
| KI-11 | closed 0.2.6 | Pixel sampling скрипт готов. VLM-оценки систематически отклоняются от ground truth на 30-100+ RGB точек. |
| KI-10 | new 0.2.3 | Каталог измеряет placement footprint, не sprite bounds. |
| KI-12 | new 0.2.6 | Marble-серия: pixel-sampled RGB (76-196 brown range) радикально отличается от VLM-оценок (210-230 light gray). Только Marble Table placement 1 даёт bright cream (237,208,169); остальные placements попали на тени/края. Нужна manual калибровка или больший sampling radius для Marble-декораций. |

### KI-2 (обновлено 0.2.6) — холодная палитра 2B

| Роль | Декорация | RGB | Источник |
|------|-----------|-----|----------|
| white | Marble Fountain | (110,103,76) brown | PIXEL 0.2.6 — НЕ белый, Marble-серия проблемна (KI-12) |
| silver | Marble Table | (196,170,136) cream | PIXEL 0.2.6 — ближе к cream, не silver |
| gray | Marble Bench | (79,64,45) brown | PIXEL 0.2.6 — НЕ gray |
| gray alt | Marble Walls | (76,68,52) brown | PIXEL 0.2.6 — НЕ gray |
| black | Small Coastal Stone | (81,80,60) dark | PIXEL 0.2.6, подтверждает VLM 0.2.5 (85,75,70) |
| red | Maraket Rubble | (125,112,87) brown | PIXEL 0.2.6 — НЕ reddish (VLM 0.2.5 (153,78,68) был шумным) |
| skin | TODO_SKIN_DECORATION | (228,200,178) | НЕ найдено — Sand Tussock (112,99,79) слишком тёмный olive-tan |

**Что закроет KI-2 полностью:** новая peach/tan декорация из другого
убежища. Текущие 28 art-декораций не содержат подходящего peach/tan
цвета — все либо тёмные (Stones, Rubble), либо слишком bright (Marble
Table placement 1).

### KI-10 (0.2.3) — placement vs sprite bounds

`DECORATION_FOOTPRINT_CATALOG` измеряет **placement footprint** (upper
bound на основе min pairwise distance), не реальные sprite bounds. Видимая
крона дерева выходит за placement-тайл. Все наблюдения — при `r=0`. Для
step-калибровки `img2hideout` placement footprint достаточен; для
визуального перекрытия нужны внутриигровые замеры sprite.

### KI-12 (0.2.6) — Marble-серия pixel-sampling

Pixel sampling показал, что Marble Bench/Walls/Fountain все дают тёмные
brown (76-110), а не светло-серые (210-230) как VLM сообщал в 0.2.4.
Только Marble Table placement 1 даёт bright cream (237,208,169).
Возможные причины:
1. Placement точка попадает на тень под Marble объектом, а не на
   мраморную поверхность.
2. Marble декорации имеют большую dark base + light top, и sampling
   radius 4 wu центрирован на нижней части.

**Что закроет KI-12:** manual калибровка через `--calibration` с 3+
anchors + больший `--sample-radius-wu` (8-12), либо интерактивный
выбор точек на спрайте Marble-декораций.

## Что улучшать дальше (не в этой итерации)

- **Manual calibration JSON для каждого скриншота.** Auto-calibration
  достаточно точна (Stash даёт believable brown во всех 7 скриншотах),
  но для Marble-серии (KI-12) нужна manual калибровка с интерактивным
  выбором anchor точек на скрайтшоте. Шаблон:
  `scripts/calibrations/<stem>.json` с 3+ anchors (Stash, Waypoint,
  NPC). Закроет KI-12.
- **Multi-pass: outline + fill.** Сначала контур, потом заливка —
  узнаваемость фигур сильно вырастет. Реализуется в `img2hideout.py`
  через `outline_color` + двухпроходной рендер. На контуре — только
  small-декорации (1 тайл), на fill — средние/крупные. Использует
  `DECORATION_FOOTPRINT_CATALOG`.
- **Drawing primitives из декораций.** Отдельная будущая задача (по
  запросу пользователя): научить конвейер «рисовать» декорациями базовые
  элементы картин — прямые/кривые линии, круг (контур), круг с заливкой,
  S-образную змейку, полосу с тремя контурами и заполнением. Подразумевает
  placement нескольких декораций в одной точке с разными углами поворота
  и/или наслоением для плотных равномерных текстур. Зафиксировать как
  отдельный epic после multi-pass.
- **Замер sprite bounds.** Расширить каталог полем `sprite_bounds_wu`
  отдельно от placement footprint. Закрывает KI-10.
- **Новая peach/tan декорация для 'skin' role.** Найти в другом убежище
  декорацию с RGB ~ (228,200,178). Закроет KI-2.
- **Поддержка нескольких убежищ.** Сейчас `NAMED_BOUNDS` содержит только
  `canal`. Добавлять новые по мере появления экспортов.
- **SVG / Lua экспорт** — для ручной доводки.

## Базовые принципы при правках

1. **Сначала в STATUS.md, потом фикс.** Новый баг → новый KI-N → потом код.
2. **Никогда не ломать существующие тесты.** Все новые опции — opt-in.
3. **Никогда не выдумывать хеши.** Нет в `KNOWN_HASHES` → помечаем unknown.
4. **RGB-значения — с указанием источника и даты.** VLM-замеры помечать
   `VLM <version>, <date>`. Pixel-sampled — `PIXEL <version>, <date>`.
   Если VLM и PIXEL конфликтуют — доверять PIXEL (KI-11 закрыт).
5. **Документация короткая.** Этот файл — не больше 100 строк.
6. **Каталог размеров — sync с исходниками.** При добавлении размещений
   в `исходники/` перезапускать `scripts/measure_decorations.py` и
   обновлять `DECORATION_FOOTPRINT_CATALOG`. Тест
   `test_sample_counts_match_real_exports` упадёт при рассинхроне.
