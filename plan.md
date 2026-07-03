StarRupture 产线规划 Agent 项目设计文档（v1）

1. 项目目标

构建一个面向游戏 StarRupture 的本地智能规划助手，用于辅助玩家进行产线自动化规划。用户通过聊天方式提出需求，例如：

* “我要每分钟生产 60 个某物品”
* “我已经有 2 条陶瓷线和 1 条塑料线，帮我补足电池产线”
* “尽量复用现有工厂，不够的部分再新增建筑”

系统应能：

1. 查询 StarRupture 的物品、配方、建筑和资源信息。
2. 将目标产物递归展开为完整依赖链。
3. 计算所需建筑数量、上游中间件和原始资源需求。
4. 记忆用户已经建成的工厂与产线状态。
5. 基于已有工厂做增量补线规划，而不是每次从零开始。
6. 通过聊天窗口（后期由 OpenClaw 提供）调用技能组，输出自然语言规划结果。

⸻

2. 产品定位

本项目不是单纯的“StarRupture 配方计算器”，而是一个 StarRupture 工厂规划 Agent。

与普通网页计算器相比，本项目的差异化能力是：

2.1 长期工厂记忆

能够记住玩家已有的工厂状态，例如：

* 某条线生产什么
* 有多少台建筑
* 产能是多少
* 位于哪个厂区
* 是否专供某条下游产线

2.2 增量补线规划

用户提出新目标时，不是重算一套全新工厂，而是：

* 先识别已有可复用产能
* 计算缺口
* 给出新增建筑和新增上游的方案

2.3 聊天式规划

用户不需要手工拖节点或填写表格，可以直接用自然语言提出需求。

2.4 后续可扩展到布局建议

在第一版实现产能规划后，后续可增加模块化布局建议、厂区划分、上下游分组等能力。

⸻

3. 技术路线总览

3.1 已确定的技术选型

核心语言

* Python 3.12+

原因：

* 用户熟悉 Python，能阅读和排查错误
* 适合做数据处理、算法、CLI 和 MCP 服务
* 与 Codex 协作开发成本较低

核心框架

* Pydantic v2：定义数据模型
* PydanticAI：构建 Agent 和结构化工具调用层
* SQLite：存储工厂状态、偏好、规划快照
* Typer：本地 CLI
* pytest：单元测试

Agent / 开发工具 / 使用入口

* Codex：开发阶段主力 coding agent，用于生成代码、补全结构、修 bug、写测试
* OpenClaw：后期作为聊天窗口和技能组入口使用，不承担核心业务逻辑
* MCP（Model Context Protocol）：作为技能暴露方式，让 OpenClaw / Codex / 其他客户端都能调用同一组工具

⸻

3.2 架构原则

本项目采用 “核心规划引擎与聊天入口分离” 的架构。

不做的事

* 不把核心规划逻辑直接写进 OpenClaw skill prompt
* 不把核心能力依赖在某个单一聊天平台里
* 不先做复杂 GUI 再补算法

要做的事

* 先实现可测试的 Python 核心规划引擎
* 再把能力包装成 MCP tools
* 最后由 OpenClaw 作为聊天窗口来调用这些 tools

⸻

4. 整体系统架构

整个项目分为 4 层：

4.1 第一层：游戏知识层（静态数据库）

负责保存 StarRupture 的游戏资料：

* 物品
* 配方
* 建筑
* 建筑分类
* 资源节点类型
* 建筑速度、等级、类别

数据来源：

* 手工整理
* StarRupture 社区 planner / calculator 的公开数据结构
* 后续可写导入脚本

4.2 第二层：规划核心层（Planner Core）

负责核心业务逻辑：

* 配方查询
* 依赖展开
* 建筑数量计算
* 工厂记忆读写
* 增量补线规划

这一层必须是纯 Python、可单元测试、可脱离聊天环境独立运行。

4.3 第三层：MCP 工具层

把规划核心暴露成一组标准化工具，例如：

* get_recipe
* expand_production
* plan_production
* upsert_factory_line

OpenClaw / Codex / 未来的 Web UI 都调用这一层。

4.4 第四层：聊天入口 / 客户端层

由 OpenClaw 负责：

* 用户聊天窗口
* 调用 MCP 工具
* 组织自然语言结果
* 后续可能接入其他聊天客户端

⸻

5. 核心能力拆分：技能组设计

本项目拆成 6 个核心技能 + 1 个总控技能。

⸻

5.1 技能 1：recipe_knowledge

作用

负责回答“是什么”的问题：

* 某物品怎么做
* 某配方需要什么原料
* 某建筑能生产什么
* 某资源由什么建筑采集

典型输入

* “电池怎么做？”
* “Furnace v2 能做什么？”
* “某中间件的前置是什么？”

核心输出

* 物品信息
* 配方信息
* 建筑信息

对应核心接口

* get_item(item_name_or_id)
* get_recipe(item_name_or_recipe_id)
* get_building(building_name_or_id)

⸻

5.2 技能 2：dependency_planner

作用

将目标产物按目标速率递归展开成完整依赖链。

例如：

* 输入：Battery 60/min
* 输出：
    * Battery 60/min
    * 上游中间件需求
    * 更上游板材/化工品需求
    * 最终矿石/气体/原始资源需求

核心职责

* 找到目标物品的配方
* 计算单位时间产量
* 倒推所需配方执行次数
* 递归展开所有输入物
* 汇总需求

对应核心接口

* expand_production(target_item, target_rate, expand_to="raw")

⸻

5.3 技能 3：factory_calculator

作用

根据需求速率换算建筑数量。

例如：

* 铁板需要 180/min
* 单台 Furnace v2 产能 30/min
* 则需要 6 台 Furnace v2

核心职责

* 计算单机产能
* 根据目标速率计算建筑数量
* 输出每个中间件对应的建筑配置

对应核心接口

* calculate_buildings(requirements)

⸻

5.4 技能 4：factory_memory

作用

记忆玩家当前已经建成的产线。

必须支持的能力

1. 新增产线
2. 修改产线
3. 删除产线
4. 查询所有产线
5. 汇总可用供给

典型数据

* 产线名称
* 产出物
* 使用配方
* 建筑类型
* 建筑数量
* 实际产能
* 所属厂区
* 是否运行中

对应核心接口

* upsert_factory_line(...)
* delete_factory_line(factory_id)
* list_factory_lines()
* get_supply_summary()

⸻

5.5 技能 5：gap_planner

作用

在已有产线基础上，计算“还差什么”。

例如用户说：

* “我要 60/min Battery”
* “我已经有 30/min Plastic 和 60/min Ceramic”

系统要回答：

* 总需求是多少
* 已有供给能覆盖多少
* 还缺哪些中间件
* 需要新增哪些建筑

核心逻辑

* 先调用 dependency_planner 得到总需求
* 再读取 factory_memory 中的已有供给
* 做差值得到新增需求
* 再交给 factory_calculator 算新增建筑数量

对应核心接口

* plan_gap(target_item, target_rate, use_existing=True)

⸻

5.6 技能 6：layout_advisor

作用

提供文字化布局建议和模块化组织建议。

第一版不做精确平面图，但要支持：

* 按工艺阶段分组：Extraction / Processing / Crafting
* 按模块拆分：上游板材模块、化工模块、最终装配模块
* 给出厂区划分建议
* 提示哪些产线应贴邻布局

第一版定位

先做“文本布局建议”而不是图形化编辑器。

⸻

5.7 总控技能：plan_factory

作用

对外暴露的主技能，负责把用户自然语言需求编排成完整规划。

典型流程

1. 识别目标产物和目标速率
2. 调用 dependency_planner
3. 调用 factory_memory
4. 调用 gap_planner
5. 调用 factory_calculator
6. 调用 layout_advisor
7. 输出最终自然语言结果

⸻

6. 规划引擎的数据模型设计

数据分为 静态游戏数据库 和 用户工厂状态 两类。

⸻

6.1 静态游戏数据库

建议最少包含以下 3 类数据：

6.1.1 items

记录所有物品。

建议字段：

* id
* name
* category
* is_raw_resource
* stack_size（可选）
* notes（可选）

示例：

{
  "id": "wolfram_plate",
  "name": "Wolfram Plate",
  "category": "intermediate",
  "is_raw_resource": false
}

6.1.2 recipes

记录配方。

建议字段：

* id
* name
* building_id
* time_seconds
* inputs
* outputs
* recipe_type
* unlock_tier（可选）

示例：

{
  "id": "wolfram_plate_recipe",
  "name": "Wolfram Plate",
  "building_id": "furnace_v2",
  "time_seconds": 4,
  "inputs": [
    {"item_id": "wolfram_ore", "amount": 2}
  ],
  "outputs": [
    {"item_id": "wolfram_plate", "amount": 1}
  ],
  "recipe_type": "processing"
}

6.1.3 buildings

记录建筑信息。

建议字段：

* id
* name
* category
* building_class
* tier
* speed_multiplier
* supported_recipe_types

示例：

{
  "id": "furnace_v2",
  "name": "Furnace v2",
  "category": "processing",
  "building_class": "furnace",
  "tier": 2,
  "speed_multiplier": 1.5,
  "supported_recipe_types": ["processing", "smelting"]
}

⸻

6.2 用户工厂状态数据库

用于记忆用户真实游戏档中的工厂状态。

建议核心表：factory_lines

每条记录至少包含：

* factory_id
* name
* item_id
* recipe_id
* building_id
* building_count
* clock_rate
* actual_rate_per_min
* zone
* status
* notes

示例：

{
  "factory_id": "plastic_line_01",
  "name": "主基地塑料线",
  "item_id": "plastic",
  "recipe_id": "plastic_default",
  "building_id": "chemical_plant_v1",
  "building_count": 4,
  "clock_rate": 1.0,
  "actual_rate_per_min": 60,
  "zone": "主基地西区",
  "status": "running",
  "notes": "主要供给电池与电子区"
}

⸻

7. 核心算法设计

⸻

7.1 配方展开算法（dependency expansion）

输入：

* 目标物品
* 目标速率

输出：

* 完整依赖树
* 汇总需求表

核心逻辑：

1. 查找目标物品配方
2. 根据配方产量和时间计算每次生产速率
3. 倒推所需配方执行次数
4. 对每个输入物递归展开
5. 汇总所有节点

停止条件：

* 遇到原始资源
* 或达到用户指定的 expand_to 层级

⸻

7.2 单机产能计算

统一公式：

单机产能（每分钟） =
(配方产出数量 / 配方时间秒) × 建筑速度倍率 × 60

如果未来支持：

* 模组
* 科技加成
* 超频
* 建筑等级差异

则继续乘以对应倍率。

⸻

7.3 建筑数量换算

建筑数量 =
ceil(目标速率 / 单机产能)

⸻

7.4 已有供给抵扣

先计算总需求，再从工厂记忆中汇总已有供给，做差得到新增需求。

公式：
新增需求 = max(0, 总需求 - 已有供给)

第一版采用**“通用供给池”**策略：

* 假设已有某物品产能都可用于当前规划
* 暂不追踪真实物流连接

后续可扩展成：

* 指定某条线专供某下游
* 厂区级供给池
* 总线制 / 模块制约束

⸻

8. 项目目录设计（第一版）

项目名建议：starrupture_agent

目录结构如下：

starrupture_agent/
├─ README.md
├─ pyproject.toml
├─ .env.example
├─ starrupture_agent/
│  ├─ __init__.py
│  │
│  ├─ game_db/
│  │  ├─ items.json
│  │  ├─ recipes.json
│  │  ├─ buildings.json
│  │  ├─ importers/
│  │  │  └─ ...
│  │  └─ loaders.py
│  │
│  ├─ models/
│  │  ├─ game_models.py
│  │  ├─ factory_models.py
│  │  ├─ planner_models.py
│  │  └─ tool_models.py
│  │
│  ├─ planner_core/
│  │  ├─ recipe_service.py
│  │  ├─ dependency_service.py
│  │  ├─ calculator_service.py
│  │  ├─ memory_service.py
│  │  ├─ gap_service.py
│  │  ├─ layout_service.py
│  │  └─ plan_service.py
│  │
│  ├─ storage/
│  │  ├─ db.py
│  │  ├─ repositories.py
│  │  └─ migrations/
│  │
│  ├─ mcp_server/
│  │  ├─ server.py
│  │  ├─ tool_recipe.py
│  │  ├─ tool_expand.py
│  │  ├─ tool_calculate.py
│  │  ├─ tool_factory_memory.py
│  │  ├─ tool_gap.py
│  │  └─ tool_plan.py
│  │
│  ├─ cli/
│  │  └─ main.py
│  │
│  ├─ agent/
│  │  ├─ planner_agent.py
│  │  └─ prompts.py
│  │
│  └─ openclaw_adapter/
│     ├─ skill_manifest.example.json
│     └─ README.md
│
└─ tests/
   ├─ test_recipe_service.py
   ├─ test_dependency_service.py
   ├─ test_calculator_service.py
   ├─ test_gap_service.py
   └─ test_memory_service.py

⸻

9. 各模块职责

⸻

9.1 game_db/

负责 StarRupture 静态数据：

* 物品
* 配方
* 建筑
* 数据导入脚本

第一版目标

先手工整理最常用的一批物品和配方，跑通全流程，再逐步扩充。

⸻

9.2 models/

统一定义 Pydantic 数据模型，避免业务层乱用 dict。

建议至少包含：

game_models.py

* Item
* Recipe
* RecipeIO
* Building

factory_models.py

* FactoryLine
* FactoryLineCreate
* FactorySupplySummary

planner_models.py

* ProductionNode
* ProductionRequirement
* BuildingPlan
* GapPlan
* ProductionPlanResult

tool_models.py

* 各 MCP tool 的输入输出模型

⸻

9.3 planner_core/

项目核心业务层，必须可脱离聊天独立运行。

recipe_service.py

* 查物品 / 配方 / 建筑
* 按物品找默认配方

dependency_service.py

* 递归展开需求
* 生成依赖树和需求汇总

calculator_service.py

* 计算单机产能
* 计算建筑数量
* 输出建筑规划结果

memory_service.py

* 增删改查工厂产线
* 汇总已有供给

gap_service.py

* 读取已有供给
* 计算新增需求
* 输出增量补线结果

layout_service.py

* 根据规划结果给出文本布局建议

plan_service.py

* 聚合以上服务，形成完整 plan_factory 结果

⸻

9.4 storage/

负责 SQLite 连接、仓储层和迁移。

第一版建议

可以先简单一点：

* 使用 SQLite
* 用 SQLAlchemy / SQLModel 建表
* 暂不做复杂迁移系统也可以

但要保证 factory_lines 能稳定持久化。

⸻

9.5 mcp_server/

把核心能力包装成 MCP 工具。

第一版至少暴露以下工具：

* get_recipe
* expand_production
* calculate_buildings
* list_factory_lines
* upsert_factory_line
* delete_factory_line
* get_supply_summary
* plan_gap
* plan_production

⸻

9.6 cli/

提供本地命令行入口，便于在没有 OpenClaw 的情况下直接调试。

建议命令示例：

starrupture plan "Battery" --rate 60
starrupture line add --item Plastic --rate 60 --building chemical_plant_v1 --count 4
starrupture line list
starrupture recipe "Battery"

CLI 是开发阶段非常重要的调试入口。

⸻

9.7 agent/

放总控 Agent 逻辑。

作用

* 接受自然语言
* 识别目标产物、速率、约束
* 调用规划服务 / MCP 工具
* 组织最终回复文本

第一版建议

即使有 PydanticAI，也不要把业务逻辑写进 prompt。
Agent 只做“理解和编排”，不做核心计算。

⸻

9.8 openclaw_adapter/

后续接入 OpenClaw 的配置和说明。

第一版只需预留

* skill manifest 示例
* MCP server 的接入说明
* 不需要一开始就完整实现 OpenClaw 集成

⸻

10. MCP 工具设计

建议第一版对外暴露以下工具。

⸻

10.1 get_recipe

输入

* item_name_or_id

输出

* 物品基本信息
* 配方
* 使用建筑
* 输入输出

⸻

10.2 expand_production

输入

* target_item
* target_rate
* expand_to

输出

* 依赖树
* 汇总需求表

⸻

10.3 calculate_buildings

输入

* 若干需求项（物品 + 速率）

输出

* 每个物品对应的建筑方案

⸻

10.4 upsert_factory_line

输入

* 产线信息

输出

* 更新后的产线记录

⸻

10.5 list_factory_lines

输出

* 当前已记录的所有产线

⸻

10.6 delete_factory_line

输入

* factory_id

输出

* 删除结果

⸻

10.7 get_supply_summary

输出

* 当前所有物品的总供给汇总

⸻

10.8 plan_gap

输入

* target_item
* target_rate
* use_existing

输出

* 总需求
* 已有供给
* 新增需求
* 新增建筑建议

⸻

10.9 plan_production

输入

* target_item
* target_rate
* use_existing
* 可选约束（未来扩展）

输出

* 完整规划结果
* 文字总结
* 建筑方案
* 布局建议

⸻

11. 第一版开发顺序（非常重要）

为了控制复杂度，项目必须分阶段开发。

⸻

阶段 1：做最小可用规划器（MVP）

目标：能查配方、能算总需求、能算建筑数量、能输出完整新建方案

阶段 1 必做内容

1. 静态数据库：items / recipes / buildings
2. recipe_service
3. dependency_service
4. calculator_service
5. plan_service
6. CLI 命令：recipe / expand / plan
7. MCP tools：
    * get_recipe
    * expand_production
    * calculate_buildings
    * plan_production

阶段 1 不做的事

* 不做复杂记忆
* 不做 OpenClaw 集成
* 不做布局图形化
* 不做真实物流追踪

⸻

阶段 2：加入工厂记忆与增量补线

目标：不再每次从零规划，而是能复用已有工厂

阶段 2 必做内容

1. SQLite 工厂状态表
2. memory_service
3. gap_service
4. MCP tools：
    * upsert_factory_line
    * list_factory_lines
    * delete_factory_line
    * get_supply_summary
    * plan_gap

阶段 2 体验目标

用户可以说：

* “我已经有 60/min Plastic”
* “把主基地铁板线记录下来”
* “在现有基础上补足 120/min Battery”

⸻

阶段 3：布局建议与 OpenClaw 集成

目标：从“计算器”升级成“聊天式规划助手”

阶段 3 内容

1. layout_service
2. OpenClaw 接入 MCP server
3. 对话式规划
4. 模块化建议与厂区划分建议
5. 方案快照 / 历史记录（可选）

⸻

12. 对参考项目的吸收策略

目前已经确认 StarRupture 社区存在一些 planner / calculator 项目。它们的主要价值不是“直接拿来跑 Python”，而是提供：

1. 游戏静态数据结构参考
2. planner 功能边界参考
3. 节点图 / 模块化组织思路

对本项目的吸收原则

* 借数据模型，不照搬前端实现
* 借 planner 功能边界，不依赖其 UI 架构
* 借节点/模块组织思路，用于后续 layout_advisor
* 工厂长期记忆和增量补线由本项目自行设计

⸻

13. 给 Codex 的实现要求

Codex 在实现本项目时应遵循以下原则：

13.1 先保证核心层独立可运行

在没有 OpenClaw 的情况下，也必须能通过 CLI 和测试运行规划流程。

13.2 业务逻辑全部落在 planner_core/

不要把核心计算写进 MCP 层、CLI 层或 Agent prompt 中。

13.3 所有输入输出都使用 Pydantic 模型

避免随意拼 dict，方便后续 MCP、CLI、测试复用。

13.4 先实现确定性规划，再做复杂优化

第一版只做：

* 配方展开
* 机器换算
* 已有供给抵扣

不要一开始就做线性规划、PDDL、复杂多工厂优化。

13.5 先覆盖最常用物品和配方

不要求第一天就录完整游戏数据库。先覆盖常用产线，打通全流程，再逐步扩充。

13.6 每个核心服务必须有单元测试

至少测试：

* 配方查询
* 需求展开
* 建筑数量换算
* 供给抵扣
* 工厂记忆增删改查

⸻

14. 第一版完成标准（Definition of Done）

当以下目标全部满足时，视为第一版可用：

核心能力

1. 可以查询指定物品的配方
2. 可以对目标产物做完整依赖展开
3. 可以输出所需中间件和原始资源需求
4. 可以计算每种需求对应的建筑数量
5. 可以通过 CLI 执行完整规划

工厂记忆（第二阶段完成标准）

6. 可以记录和列出已有产线
7. 可以汇总已有供给
8. 可以在现有供给基础上做增量补线规划

集成能力

9. MCP server 能稳定暴露核心工具
10. OpenClaw 后续可直接接入 MCP tools

⸻

15. 当前推荐的实施顺序（最终版）

第一步

搭建项目脚手架与 Pydantic 模型。

第二步

整理第一批 StarRupture 静态数据：

* 常用物品
* 常用配方
* 常用建筑

第三步

实现并测试：

* recipe_service
* dependency_service
* calculator_service
* plan_service

第四步

实现 CLI 和第一批 MCP tools。

第五步

接入 SQLite，完成：

* memory_service
* gap_service

第六步

再考虑 OpenClaw 作为聊天窗口接入。

⸻

16. 项目一句话总结

本项目是一个以 Python 为核心、通过 MCP 暴露技能、由 OpenClaw 提供聊天入口的 StarRupture 工厂规划 Agent；第一阶段先做确定性的产能规划引擎，第二阶段加入工厂记忆与增量补线，第三阶段再扩展为聊天式长期工厂助手。