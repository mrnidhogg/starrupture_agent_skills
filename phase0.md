Phase 0：项目脚手架与基础规范

0.1 目标

搭建项目结构、依赖管理、测试框架、CLI 入口、基础模型目录，让后续所有功能有固定落点。

0.2 Codex 需要完成的任务

任务 A：创建项目目录

建立以下目录结构：

starrupture_agent_skills/
├─ pyproject.toml
├─ README.md
├─ .gitignore
├─ starrupture_agent_skills/
│  ├─ __init__.py
│  ├─ game_db/
│  ├─ models/
│  ├─ planner_core/
│  ├─ storage/
│  ├─ mcp_server/
│  ├─ cli/
│  ├─ agent/
│  └─ openclaw_adapter/
└─ tests/

任务 B：配置依赖

建议先加入：

* pydantic
* typer
* pytest
* sqlalchemy（或 sqlmodel）
* rich（可选，用于 CLI 输出）
* pydantic-settings（可选）

任务 C：创建 CLI 骨架

至少要有：

* starrupture --help
* 一个空的 plan 命令
* 一个空的 recipe 命令

任务 D：建立基础模型文件

先创建空文件：

* models/game_models.py
* models/factory_models.py
* models/planner_models.py

任务 E：配置测试框架

确保 pytest 可以运行，并至少有一个最简单的 smoke test。

⸻

0.3 Phase 0 的交付物

* 完整项目目录
* 可安装依赖的 pyproject.toml
* 可运行的 CLI 骨架
* pytest 可执行
* README 里有基本启动说明

⸻

0.4 验收标准

验收 1：项目能安装

运行安装命令后无报错。

验收 2：CLI 可调用

执行：

starrupture --help
starrupture plan --help

能够看到帮助信息。

验收 3：测试可运行

执行：

pytest

至少有 1 个通过的测试。

⸻

0.5 给 Codex 的提示词建议

创建 starrupture_agent_skills 项目脚手架，使用 Python 3.12。生成 pyproject.toml、README、基础包目录、tests 目录、Typer CLI 骨架和 pytest 配置。要求项目能通过 pytest，CLI 能显示 help。暂时不实现业务逻辑，只搭骨架。