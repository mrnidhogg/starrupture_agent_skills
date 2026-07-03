"""静态游戏数据模型（Phase 1）。

定义 StarRupture 静态知识层的 Pydantic 模型：Item / RecipeIO /
Recipe / Building。这些模型用于校验 game_db/*.json 并在规划核心层中复用。
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ItemCategory(str, Enum):
    """物品大类。"""

    RAW = "raw"
    INTERMEDIATE = "intermediate"
    FINAL = "final"


class RecipeType(str, Enum):
    """配方类别（对应可执行该配方的建筑能力）。"""

    EXTRACTION = "extraction"
    PROCESSING = "processing"
    SMELTING = "smelting"
    CHEMICAL = "chemical"
    CRAFTING = "crafting"
    ASSEMBLY = "assembly"


class Item(BaseModel):
    """一个可被生产或采集的物品。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, description="全局唯一的物品 ID。")
    name: str = Field(..., min_length=1, description="展示用名称。")
    category: ItemCategory = Field(..., description="物品大类。")
    is_raw_resource: bool = Field(
        default=False, description="是否为无需配方的原始资源。"
    )


class RecipeIO(BaseModel):
    """配方的一个输入或输出项。"""

    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(..., min_length=1, description="引用的物品 ID。")
    amount: float = Field(..., gt=0, description="每次配方执行的数量（>0）。")


class Recipe(BaseModel):
    """一条把输入物转化为输出物的配方。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, description="全局唯一的配方 ID。")
    name: str = Field(..., min_length=1, description="展示用名称。")
    building_id: str = Field(
        ..., min_length=1, description="执行该配方的建筑 ID。"
    )
    time_seconds: float = Field(
        ..., gt=0, description="单次配方执行耗时（秒，>0）。"
    )
    inputs: list[RecipeIO] = Field(
        default_factory=list, description="输入物清单（原始资源采集可为空）。"
    )
    outputs: list[RecipeIO] = Field(
        ..., min_length=1, description="输出物清单（至少一项）。"
    )
    recipe_type: RecipeType = Field(..., description="配方类别。")


class Building(BaseModel):
    """一类可执行配方的生产建筑。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, description="全局唯一的建筑 ID。")
    name: str = Field(..., min_length=1, description="展示用名称。")
    category: str = Field(..., min_length=1, description="建筑用途分类。")
    building_class: str = Field(
        ..., min_length=1, description="建筑族类（如 furnace / miner）。"
    )
    tier: int = Field(..., ge=1, description="建筑等级（>=1）。")
    speed_multiplier: float = Field(
        default=1.0, gt=0, description="速度倍率（>0），单机产能换算用。"
    )
