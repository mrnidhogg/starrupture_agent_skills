# starrupture_agent_skills

StarRupture 工厂产线规划 Agent。以 Python 为核心构建确定性的产能规划引擎，
后续通过 MCP 暴露技能，由 OpenClaw 提供聊天入口。

当前进度：**Phase 0 —— 项目脚手架**。仅搭建目录结构、依赖管理、CLI 骨架与测试框架，
尚未实现业务逻辑。详细设计见 [plan.md](plan.md)，阶段任务见 [phase0.md](phase0.md)。

## 环境要求

- Python 3.12+

## 安装

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## CLI 使用

安装后可通过 `starrupture` 命令调用：

```bash
starrupture --help
starrupture plan --help
starrupture plan Battery --rate 60
starrupture recipe Battery
```

> Phase 0 阶段 CLI 命令仅为占位骨架，会打印提示信息，规划逻辑将在后续阶段实现。

## 运行测试

```bash
pytest
```

## 项目结构

```text
starrupture_agent_skills/
├─ game_db/            # 静态游戏数据（物品/配方/建筑）与加载器
├─ models/             # Pydantic 数据模型
├─ planner_core/       # 规划核心业务层（纯 Python，可独立测试）
├─ storage/            # SQLite 持久化层
├─ mcp_server/         # MCP 工具层
├─ cli/                # 本地命令行入口
├─ agent/              # 总控 Agent（理解与编排）
└─ openclaw_adapter/   # OpenClaw 接入适配
```
