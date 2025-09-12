import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pdf_parser import build_foundry_scenes


def test_build_foundry_scenes():
    images = [{"name": "map.png", "path": "maps/map.png", "width": 100, "height": 200}]
    scenes = build_foundry_scenes(images, grid_size=75)
    assert scenes[0]["name"] == "map.png"
    assert scenes[0]["img"] == "maps/map.png"
    assert scenes[0]["width"] == 100
    assert scenes[0]["height"] == 200
    assert scenes[0]["grid"] == 75
    assert scenes[0]["gridType"] == 1

