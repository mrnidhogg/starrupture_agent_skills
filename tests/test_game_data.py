"""Phase 1 验收测试：静态数据加载、查询索引与非法数据报错。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from starrupture_agent_skills.game_db.loaders import (
    GameDataError,
    load_buildings,
    load_game_data,
    load_items,
    load_recipes,
)
from starrupture_agent_skills.models.game_models import ItemCategory


# ---- 验收 1：数据可加载 ----------------------------------------------------

def test_load_game_data_no_error() -> None:
    data = load_game_data()
    assert data.items and data.recipes and data.buildings


def test_individual_loaders() -> None:
    assert load_items()
    assert load_recipes()
    assert load_buildings()


def test_dataset_covers_minimum_chain() -> None:
    data = load_game_data()
    raw = [i for i in data.items if i.category is ItemCategory.RAW]
    intermediate = [
        i for i in data.items if i.category is ItemCategory.INTERMEDIATE
    ]
    final = [i for i in data.items if i.category is ItemCategory.FINAL]
    assert len(raw) >= 2
    assert len(intermediate) >= 3
    assert len(final) >= 1
    assert len({b.building_class for b in data.buildings}) >= 2


# ---- 验收 2：能按名称或 ID 查到对象 ---------------------------------------

def test_lookup_item_by_id_and_name() -> None:
    data = load_game_data()
    assert data.get_item("battery").name == "Battery"
    assert data.get_item("Battery").id == "battery"
    assert data.get_item("does_not_exist") is None


def test_lookup_recipe_and_building() -> None:
    data = load_game_data()
    assert data.get_recipe("battery_assembly").name == "Battery"
    assert data.get_building("furnace_v2").speed_multiplier == 1.5


def test_recipes_by_output_item() -> None:
    data = load_game_data()
    recipes = data.recipes_for_output("battery")
    assert [r.id for r in recipes] == ["battery_assembly"]
    assert data.recipes_for_output("copper_ore")[0].recipe_type.value == "extraction"


# ---- 验收 3：非法数据能报错 ------------------------------------------------

def _write_dataset(
    tmp_path: Path,
    items: list[dict],
    recipes: list[dict],
    buildings: list[dict],
) -> Path:
    (tmp_path / "items.json").write_text(json.dumps(items), encoding="utf-8")
    (tmp_path / "recipes.json").write_text(json.dumps(recipes), encoding="utf-8")
    (tmp_path / "buildings.json").write_text(
        json.dumps(buildings), encoding="utf-8"
    )
    return tmp_path


def test_missing_field_raises(tmp_path: Path) -> None:
    # 缺少 category 字段的物品
    bad_items = [{"id": "x", "name": "X"}]
    _write_dataset(tmp_path, bad_items, [], [])
    with pytest.raises(GameDataError) as exc:
        load_game_data(tmp_path)
    assert "items.json" in str(exc.value)


def test_duplicate_id_raises(tmp_path: Path) -> None:
    dup = [
        {"id": "dup", "name": "A", "category": "raw", "is_raw_resource": True},
        {"id": "dup", "name": "B", "category": "raw", "is_raw_resource": True},
    ]
    _write_dataset(tmp_path, dup, [], [])
    with pytest.raises(GameDataError) as exc:
        load_game_data(tmp_path)
    assert "重复 ID" in str(exc.value)


def test_dangling_reference_raises(tmp_path: Path) -> None:
    items = [
        {"id": "a", "name": "A", "category": "raw", "is_raw_resource": True}
    ]
    buildings = [
        {
            "id": "b1",
            "name": "B1",
            "category": "smelting",
            "building_class": "furnace",
            "tier": 1,
            "speed_multiplier": 1.0,
        }
    ]
    # 输出引用了不存在的物品 ghost
    recipes = [
        {
            "id": "r1",
            "name": "R1",
            "building_id": "b1",
            "time_seconds": 1.0,
            "inputs": [],
            "outputs": [{"item_id": "ghost", "amount": 1}],
            "recipe_type": "smelting",
        }
    ]
    _write_dataset(tmp_path, items, recipes, buildings)
    with pytest.raises(GameDataError) as exc:
        load_game_data(tmp_path)
    assert "不存在的物品" in str(exc.value)


def test_not_a_json_array_raises(tmp_path: Path) -> None:
    (tmp_path / "items.json").write_text("{}", encoding="utf-8")
    (tmp_path / "recipes.json").write_text("[]", encoding="utf-8")
    (tmp_path / "buildings.json").write_text("[]", encoding="utf-8")
    with pytest.raises(GameDataError) as exc:
        load_game_data(tmp_path)
    assert "顶层应为数组" in str(exc.value)
