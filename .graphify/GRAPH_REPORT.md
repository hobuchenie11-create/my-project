# Graph Report - .  (2026-08-04)

## Corpus Check
- Corpus is ~12,049 words - fits in a single context window. You may not need a graph.

## Summary
- 107 nodes · 197 edges · 10 communities detected
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output
- Edge kinds: contains: 70 · calls: 52 · implements: 28 · references: 22 · shares_data_with: 11 · conceptually_related_to: 7 · semantically_similar_to: 5 · rationale_for: 2


## Input Scope
- Requested: tracked
- Resolved: tracked (source: cli)
- Included files: 9 · Candidates: 15
- Excluded: 12 untracked · 117 ignored · 0 sensitive · 0 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.
## God Nodes (most connected - your core abstractions)
1. `init()` - 10 edges
2. `openOrder()` - 9 edges
3. `persistCart()` - 8 edges
4. `toast()` - 7 edges
5. `init()` - 7 edges
6. `Витрина магазина «Алиса»` - 7 edges
7. `Каталог с фильтрами` - 7 edges
8. `Оформление заказа в три шага` - 7 edges
9. `renderTable()` - 6 edges
10. `setStatus()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `setStatus()` --implements--> `Статусы заказа`  [INFERRED]
  /home/user/my-project/assets/js/orders.js → orders/index.html
- `bundle()` --implements--> `Сборка в один самодостаточный файл`  [INFERRED]
  /home/user/my-project/build.js → README.md
- `persistCart()` --implements--> `Хранение только в браузере`  [INFERRED]
  /home/user/my-project/assets/js/app.js → README.md
- `renderCatalog()` --implements--> `Каталог с фильтрами`  [INFERRED]
  /home/user/my-project/assets/js/app.js → index.html
- `renderStatic()` --implements--> `Частые вопросы`  [INFERRED]
  /home/user/my-project/assets/js/app.js → index.html

## Hyperedges (group relationships)
- **Участники оформления заказа** — checkout_flow, delivery_methods, payment_methods, promo_codes [EXTRACTED 0.90]
- **Обработка заказа у владельца** — order_pipeline, telegram_notification, orders_table, order_detail_card, csv_export, order_statuses [EXTRACTED 0.90]
- **Границы прототипа** — browser_only_storage, demo_disclaimer, production_gap, noindex_policy [INFERRED 0.85]

## Communities

### Community 0 - "Каталог и данные магазина"
Cohesion: 0.12
Nodes (20): Корзина-шторка, Каталог с фильтрами, Правка содержимого через data.js, Частые вопросы, renderBrand(), renderCart(), renderStatic(), BRAND (+12 more)

### Community 1 - "Журнал заказов"
Cohesion: 0.21
Nodes (19): applyTheme(), bind(), closeOrder(), exportCsv(), fmtAgo(), init(), openOrder(), orderDate() (+11 more)

### Community 2 - "Сборка и публикация страниц"
Cohesion: 0.15
Nodes (15): between(), bundle(), fs, orders, ordersPage, path, read(), shop (+7 more)

### Community 3 - "Обработка заказа и границы прототипа"
Cohesion: 0.18
Nodes (10): Хранение только в браузере, Выгрузка заказов в таблицу, Оговорка о демонстрации, DEMO_ORDERS, ORDER_STATUSES, Путь заказа от покупателя до журнала, Статусы заказа, Таблица заказов с поиском (+2 more)

### Community 4 - "Доставка и оплата"
Cohesion: 0.28
Nodes (9): Оформление заказа в три шага, Способы доставки, deliveryPrice(), renderCheckout(), renderSteps(), submitOrder(), DELIVERY, PAYMENT (+1 more)

### Community 5 - "Запуск витрины и тема"
Cohesion: 0.29
Nodes (7): Плитки категорий, applyTheme(), bind(), init(), renderCategoryTiles(), renderFilterChips(), Переключатель светлой и тёмной темы

### Community 6 - "Проверка формы и служебные слои"
Cohesion: 0.33
Nodes (2): markError(), validateStep()

### Community 7 - "Корзина покупателя"
Cohesion: 0.50
Nodes (5): addToCart(), persistCart(), removeLine(), setQty(), toast()

### Community 8 - "Открытие карточек и окон"
Cohesion: 0.40
Nodes (5): closeLayer(), openCheckout(), openLayer(), openProduct(), Карточка товара

### Community 9 - "Отрисовка каталога и избранное"
Cohesion: 0.50
Nodes (4): renderCatalog(), renderCounters(), toggleFav(), visibleProducts()

## Knowledge Gaps
- **8 isolated node(s):** `CATEGORIES`, `fs`, `path`, `shop`, `orders` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Проверка формы и служебные слои`** (2 nodes): `markError()`, `validateStep()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Витрина магазина «Алиса»` connect `Сборка и публикация страниц` to `Проверка формы и служебные слои`, `Каталог и данные магазина`?**
  _High betweenness centrality (0.187) - this node is a cross-community bridge._
- **Why does `Журнал заказов владельца` connect `Сборка и публикация страниц` to `Каталог и данные магазина`, `Журнал заказов`, `Обработка заказа и границы прототипа`, `Запуск витрины и тема`?**
  _High betweenness centrality (0.182) - this node is a cross-community bridge._
- **Why does `openOrder()` connect `Журнал заказов` to `Открытие карточек и окон`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `openOrder()` (e.g. with `openProduct()` and `Карточка заказа со шкалой выполнения`) actually correct?**
  _`openOrder()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CATEGORIES`, `fs`, `path` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Каталог и данные магазина` be split into smaller, more focused modules?**
  _Cohesion score 0.12380952380952381 - nodes in this community are weakly interconnected._