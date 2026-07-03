"""游戏静态数据加载器与查询索引（Phase 1）。

从 game_db/*.json 读取物品 / 配方 / 建筑，使用 Pydantic 校验为结构化对象，
并构建基础查询索引。对 ID 重复、缺字段、引用缺失等问题抛出清晰异常。
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from starrupture_agent_skills.models.game_models import (
    Building,
    Item,
    Recipe,
)

# game_db 目录（本文件所在目录）。
DATA_DIR = Path(__file__).resolve().parent

ITEMS_FILE = "items.json"
RECIPES_FILE = "recipes.json"
BUILDINGS_FILE = "buildings.json"

TModel = TypeVar("TModel", bound=BaseModel)


class GameDataError(Exception):
    """加载或校验游戏静态数据时发生的错误。"""


def _read_json_array(path: Path) -> list[dict[str, Any]]:
    """读取一个 JSON 文件并确保其顶层是对象数组。"""
    if not path.exists():
        raise GameDataError(f"数据文件不存在: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GameDataError(f"JSON 解析失败 ({path.name}): {exc}") from exc
    if not isinstance(raw, list):
        raise GameDataError(
            f"数据文件顶层应为数组: {path.name}（实际为 {type(raw).__name__}）"
        )
    return raw


def _parse_models(
    rows: list[dict[str, Any]], model: type[TModel], source: str
) -> list[TModel]:
    """把原始字典逐条校验为 Pydantic 模型，附带行号信息。"""
    parsed: list[TModel] = []
    for index, row in enumerate(rows):
        try:
            parsed.append(model.model_validate(row))
        except ValidationError as exc:
            raise GameDataError(
                f"{source} 第 {index} 条记录校验失败:\n{exc}"
            ) from exc
    return parsed


def _index_unique_by_id(objects: list[TModel], source: str) -> dict[str, TModel]:
    """按 id 建唯一索引，遇到重复 ID 抛错。"""
    index: dict[str, TModel] = {}
    for obj in objects:
        obj_id = obj.id  # type: ignore[attr-defined]
        if obj_id in index:
            raise GameDataError(f"{source} 存在重复 ID: {obj_id!r}")
        index[obj_id] = obj
    return index


def _resolve_path(data_dir: Path | None, filename: str) -> Path:
    return (data_dir or DATA_DIR) / filename


def load_items(data_dir: Path | None = None) -> list[Item]:
    """加载并校验全部物品。"""
    rows = _read_json_array(_resolve_path(data_dir, ITEMS_FILE))
    items = _parse_models(rows, Item, "items.json")
    _index_unique_by_id(items, "items.json")
    return items


def load_recipes(data_dir: Path | None = None) -> list[Recipe]:
    """加载并校验全部配方。"""
    rows = _read_json_array(_resolve_path(data_dir, RECIPES_FILE))
    recipes = _parse_models(rows, Recipe, "recipes.json")
    _index_unique_by_id(recipes, "recipes.json")
    return recipes


def load_buildings(data_dir: Path | None = None) -> list[Building]:
    """加载并校验全部建筑。"""
    rows = _read_json_array(_resolve_path(data_dir, BUILDINGS_FILE))
    buildings = _parse_models(rows, Building, "buildings.json")
    _index_unique_by_id(buildings, "buildings.json")
    return buildings


class GameData(BaseModel):
    """一次性加载后的游戏静态数据 + 基础查询索引。"""

    model_config = {"arbitrary_types_allowed": True}

    items: list[Item]
    recipes: list[Recipe]
    buildings: list[Building]

    items_by_id: dict[str, Item]
    items_by_name: dict[str, Item]
    recipes_by_id: dict[str, Recipe]
    recipes_by_output_item: dict[str, list[Recipe]]
    buildings_by_id: dict[str, Building]

    def get_item(self, key: str) -> Item | None:
        """按 ID 或名称查物品。"""
        return self.items_by_id.get(key) or self.items_by_name.get(key)

    def get_recipe(self, recipe_id: str) -> Recipe | None:
        """按 ID 查配方。"""
        return self.recipes_by_id.get(recipe_id)

    def get_building(self, building_id: str) -> Building | None:
        """按 ID 查建筑。"""
        return self.buildings_by_id.get(building_id)

    def recipes_for_output(self, item_id: str) -> list[Recipe]:
        """查询产出指定物品的所有配方。"""
        return self.recipes_by_output_item.get(item_id, [])


def _index_by_name(items: list[Item]) -> dict[str, Item]:
    index: dict[str, Item] = {}
    for item in items:
        if item.name in index:
            raise GameDataError(f"items.json 存在重复名称: {item.name!r}")
        index[item.name] = item
    return index


def _check_references(
    items_by_id: dict[str, Item],
    recipes: list[Recipe],
    buildings_by_id: dict[str, Building],
) -> None:
    """校验配方引用的物品 / 建筑均存在。"""
    for recipe in recipes:
        if recipe.building_id not in buildings_by_id:
            raise GameDataError(
                f"配方 {recipe.id!r} 引用了不存在的建筑: {recipe.building_id!r}"
            )
        for io in (*recipe.inputs, *recipe.outputs):
            if io.item_id not in items_by_id:
                raise GameDataError(
                    f"配方 {recipe.id!r} 引用了不存在的物品: {io.item_id!r}"
                )


def load_game_data(data_dir: Path | None = None) -> GameData:
    """一次性加载全部静态数据，构建索引并做引用完整性校验。"""
    items = load_items(data_dir)
    recipes = load_recipes(data_dir)
    buildings = load_buildings(data_dir)

    items_by_id = _index_unique_by_id(items, "items.json")
    recipes_by_id = _index_unique_by_id(recipes, "recipes.json")
    buildings_by_id = _index_unique_by_id(buildings, "buildings.json")
    items_by_name = _index_by_name(items)

    _check_references(items_by_id, recipes, buildings_by_id)

    recipes_by_output_item: dict[str, list[Recipe]] = defaultdict(list)
    for recipe in recipes:
        for output in recipe.outputs:
            recipes_by_output_item[output.item_id].append(recipe)

    return GameData(
        items=items,
        recipes=recipes,
        buildings=buildings,
        items_by_id=items_by_id,
        items_by_name=items_by_name,
        recipes_by_id=recipes_by_id,
        recipes_by_output_item=dict(recipes_by_output_item),
        buildings_by_id=buildings_by_id,
    )
