"""StarRupture 规划 Agent 的本地 CLI 入口（Phase 0 骨架）。

当前仅提供命令骨架，业务逻辑将在后续阶段落在 planner_core/ 中，
CLI 层只负责解析参数并调用核心服务。
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="starrupture",
    help="StarRupture 工厂产线规划 Agent 命令行工具。",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def plan(
    target: str = typer.Argument(..., help="目标产物名称，例如 Battery。"),
    rate: float = typer.Option(
        60.0, "--rate", "-r", help="目标产能（每分钟）。"
    ),
) -> None:
    """规划目标产物的完整产线（Phase 0 占位，尚未实现）。"""
    typer.echo(
        f"[Phase 0 骨架] plan target={target!r} rate={rate}/min —— 规划逻辑尚未实现。"
    )


@app.command()
def recipe(
    item: str = typer.Argument(..., help="物品名称或 ID，例如 Battery。"),
) -> None:
    """查询指定物品的配方（Phase 0 占位，尚未实现）。"""
    typer.echo(f"[Phase 0 骨架] recipe item={item!r} —— 查询逻辑尚未实现。")


def run() -> None:
    """控制台脚本入口点。"""
    app()


if __name__ == "__main__":
    run()
