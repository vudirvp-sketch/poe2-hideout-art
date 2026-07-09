# Mosaic & Bas-Relief Recipe

Краткая памятка для композиций из декораций (портреты, барельефы, мозаики).
**Не спецификация** — это курируемый набор приёмов. Расширяй по мере visual-verification.

---

## Концепция: «Портрет из артефактов и природы»

3D-композиция на плиточном полу убежища (ракурс сверху вниз, изометрия как в PoE2).
Не плоский рисунок, а **мозаичный барельеф** из камней, ковров, растений и песка.

Целевая поза (по референсу): мужчина с короткими седыми волосами и бородой,
в очках, указательный палец правой руки касается носа.

| Зона портрета | Декорация-«роли» |
|---|---|
| Кожа лица/шеи | Maraket Ornament (плотная подложка-ковёр) |
| Тени на коже | Maraket Rubble (тёмнее, нейтрально-коричневый) |
| Борода | Seaweed (длинная «бородатая» форма) + Falling Sand (седина) |
| Череп (контур) | Medium Coastal Stone (крупные акцентные точки) |
| Седые волосы | Slender Seedling + Small Coastal Stone (светлые) + Falling Sand |
| Глаза (зрачки) | Small Coastal Stone (1 светлый + 1 тёмный) |
| Брови | Log (под углом) или ряд Small Coastal Stone |
| Улыбка | Small Coastal Stone в изогнутой линии → `bezier_curve` |
| Очки-линзы | Cave Coral (разрезанный пополам) → `thick_ring` |
| Очки-дужка | Coastal Bush (тонкие) + Slender Seedling (переносица) |
| Палец (контур) | Medium Coastal Stone (костяшки) + Log (основание) |
| Палец (ноготь) | Small Coastal Stone 1 |
| Футболка/тело | Maraket Rubble + Seaweed 8 + Pile of Leaves |
| Фон-алтарь | Cave Fossil + Summit Brazier (атмосфера) |

**Правило:** точное попадание в RGB НЕ нужно (KI-2 wontfix). Главное — различимость.

---

## Рейтинг декораций по назначению

### Для контура и «точек» (лучшие — мелкие + узнаваемой формы)

| Декорация | Применение |
|---|---|
| **Small Coastal Stone** (1–5) | Идеальные «точки», мелкие детали, зрачки |
| **Coastal Pebble** (кучи 4–7) | Тонкие едва заметные линии, затенение контура |
| **Medium Coastal Stone** (2, 3, 9) | Крупные акцентные точки, узлы контура |
| **Log 6** | Прямые линии, границы, брови |
| Slender Seedling | Ажурные/пушистые контуры (волосы) |
| Coastal Bush (малые) | То же, чуть плотнее |

**НЕ подходят для контура:** Seaweed (все), Pile of Leaves, Falling Sand,
крупные кучи Coastal Pebble (1, 2, 3, 8, 9) — слишком бесформенные.

### Для заполнения/фона (лучшие — плотные + текстурные)

| Декорация | Применение |
|---|---|
| **Coastal Pebble** (кучи 1, 2, 3, 8, 9) | Текстурированный каменистый фон |
| **Seaweed 8** | Крупная плотная куча, органический фон |
| **Pile of Leaves** (все) | «Лесная»/осенняя тема |
| **Maraket Ornament** | Готовая ровная подложка-ковёр с рисунком |
| Coastal Bush (крупные 3, 4, 5) | Эффект зарослей |
| Seaweed (1, 2, 3, 4, 12) | Разреженное заполнение |
| Falling Sand | Полупрозрачный «пыльный»/«магический» фон |

**НЕ подходят для фона:** Small Coastal Stone, Log, Maraket Rubble,
Maraket Samovar/Treasures, Cave Fossil, Marble Fountain — слишком мелкие
или имеют чёткую форму.

---

## Доступные примитивы (v0.2.9)

### Core (0.2.7) — проверено 3/5 в игре (KI-14/15 fix в 0.2.8, awaiting re-verify)

`line`, `polyline`, `hollow_circle`, `filled_circle`, `s_snake`,
`thick_line_with_contours` + курируемая `center_composition`.

### Mosaic/bas-relief (0.2.8) — Python API only, не в composition

`arc`, `rectangle`, `polygon`, `grid`.

### Mosaic v2 (0.2.9 NEW) — для портретов/барельефов

| Примитив | Зачем |
|---|---|
| `bezier_curve(p0, p1, p2, opts)` | Органические кривые: улыбка, брови, контур пальца, плечи |
| `thick_ring(cx, cy, inner_r, outer_r, outline, fill)` | Очки-линзы, глаза, декоративные рамки, нимбы |
| `thick_arc(cx, cy, radius, thickness, start, end, outline, fill)` | Дужки очков, скобки, улыбка с толщиной, арки |
| `crosshatch(x0, y0, x1, y1, opts, angle_deg)` | Текстуры: борода, волосы, тени, штриховка фона |

Демонстрация: `mosaic_composition()` — 4 новых примитива в свободной зоне холста,
не трогая `center_composition` (чтобы KI-14/15 re-verify остался чистым).

---

## Как использовать для портрета (псевдокод)

```python
from hideout_art.primitives import (
    bezier_curve, thick_ring, thick_arc, crosshatch,
    PrimitiveOptions,
)

# Улыбка — квадратичная Безье от левого уголка рта к правому
smile = bezier_curve(
    p0=(cx-15, cy+5), p1=(cx, cy+12), p2=(cx+15, cy+5),
    opts=PrimitiveOptions(decoration="Small Coastal Stone"),
)

# Очки-линзы — два толстых кольца
left_lens = thick_ring(cx-12, cy-8, inner_r=6, outer_r=10,
    outline_opts=PrimitiveOptions(decoration="Small Coastal Stone"),
    fill_opts=PrimitiveOptions(decoration="Cave Coral"))
right_lens = thick_ring(cx+12, cy-8, inner_r=6, outer_r=10, ...)

# Дужка очков — толстая дуга
temple = thick_arc(cx-12, cy-8, radius=14, thickness=4,
    start_deg=200, end_deg=340, ...)

# Борода — штриховка
beard = crosshatch(cx-18, cy+8, cx+18, cy+25,
    opts=PrimitiveOptions(decoration="Seaweed"), angle_deg=30)
```

Полная композиция портрета — **следующая итерация** (после visual-verify 0.2.9).
