Phase 1：静态游戏数据库与数据加载层

1.1 目标

建立 StarRupture 的静态数据层，包括：

* 物品 items
* 配方 recipes
* 建筑 buildings

并提供可靠的数据加载与校验。

⸻

1.2 Codex 需要完成的任务

任务 A：定义游戏数据模型

在 models/game_models.py 中定义：

Item

建议字段：

* id
* name
* category
* is_raw_resource

RecipeIO

建议字段：

* item_id
* amount

Recipe

建议字段：

* id
* name
* building_id
* time_seconds
* inputs: list[RecipeIO]
* outputs: list[RecipeIO]
* recipe_type

Building

建议字段：

* id
* name
* category
* building_class
* tier
* speed_multiplier

⸻

任务 B：准备初始 JSON 数据文件

在 game_db/ 下创建：

* items.json
* recipes.json
* buildings.json

第一版不要求完整覆盖游戏，只要先放一批可跑通规划链条的示例数据。
至少要覆盖：

* 2~3 个原始资源
* 3~5 个中间件
* 1~2 个最终产物
* 2~4 类建筑

⸻

任务 C：实现数据加载器

在 game_db/loaders.py 中实现：

* load_items()
* load_recipes()
* load_buildings()
* load_game_data()（一次性加载全部）

要求：

* 读取 JSON
* 用 Pydantic 校验
* 返回结构化对象
* 对 ID 重复 / 缺字段给出明确错误

⸻

任务 D：实现基础查询索引

建议在 loader 或独立模块中提供：

* items_by_id
* items_by_name
* recipes_by_id
* recipes_by_output_item
* buildings_by_id

⸻

1.3 Phase 1 的交付物

* game_models.py
* 三个 JSON 数据文件
* 数据加载器
* 基础查询索引

⸻

1.4 验收标准

验收 1：数据可加载

写一个测试，加载全部 JSON 数据，无异常。

验收 2：能按名称或 ID 查到对象

例如能查到：

* 某物品
* 某配方
* 某建筑

验收 3：非法数据能报错

故意给一个缺字段的测试数据，应抛出清晰异常。

⸻

1.5 给 Codex 的提示词建议

在 models/game_models.py 中定义 Item / RecipeIO / Recipe / Building 的 Pydantic 模型。创建 game_db/items.json、recipes.json、buildings.json 示例数据，并实现 game_db/loaders.py，要求能把 JSON 加载为结构化对象，支持基础索引与校验。为 loader 写 pytest。