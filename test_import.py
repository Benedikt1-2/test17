"""Tests for the keyword rules in import_recipes.py. Run with:  python -m pytest"""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import import_recipes as imp  # noqa: E402
import logic  # noqa: E402


def test_diet():
    assert imp.diet_of("1 pound chicken breast; 1 onion") == "meat"
    assert imp.diet_of("1 pound salmon; 1 lemon") == "pesce"
    assert imp.diet_of("2 eggs; 1 cup flour") == "veg"
    # plant foods with animal words in their name stay vegan
    assert imp.diet_of("1 eggplant; 1 cup coconut milk; 2 tbsp peanut butter; 1 butternut squash") == "vegan"
    assert imp.diet_of("2 cloves garlic, minced; graham crackers") == "vegan"


def test_allergens():
    assert imp.allergens_of("1 cup flour; 2 eggs; 50 g parmesan") == "Gluten,Lactose,Egg"
    assert imp.allergens_of("1 tsp nutmeg; 1 coconut") == ""
    assert imp.allergens_of("shrimp; tahini") == "Shellfish,Sesame"


def test_cuisine_and_tags():
    assert imp.cuisine_of("Chicken Tikka Masala", "Main Dishes") == "indian"
    assert imp.cuisine_of("Meatloaf", "Main Dishes") == "american"
    assert "soup" in imp.tags_of("Tomato Soup", "Soups", "tomatoes", 40)
    assert "quick" in imp.tags_of("Toast", "Breakfast", "bread", 15)


def test_minutes():
    assert imp.minutes_of(["Simmer for 20 to 25 minutes.", "Bake 1 hour."]) == 95  # 25 + 60 + 10 prep


def test_convert_gives_app_format():
    raw = pd.DataFrame([
        {"recipe_title": "Gochujang Pork Belly Bites", "category": "Air Fryer Recipes", "subcategory": "Air Fryer Recipes",
         "description": "", "ingredients": json.dumps(["1 pound pork belly", "1/4 cup gochujang", "2 tablespoons soy sauce"]),
         "directions": json.dumps(["Preheat an air fryer.", "Air fry for 10 minutes."]), "num_ingredients": 3, "num_steps": 2},
        {"recipe_title": "Chocolate Cake", "category": "Desserts", "subcategory": "Cakes",
         "description": "", "ingredients": json.dumps(["flour"]), "directions": json.dumps(["Bake."]),
         "num_ingredients": 1, "num_steps": 1},
    ])
    out = imp.convert(raw)
    assert list(out["name"]) == ["Gochujang Pork Belly Bites"]  # the dessert is filtered out
    r = out.iloc[0].to_dict()
    assert set(r) == {"id", "name", "cuisine", "diet", "minutes", "allergens", "tags", "ingredients", "steps"}
    assert (r["cuisine"], r["diet"]) == ("asian", "meat")
    assert r["ingredients"].split("; ")[0] == "1 pound pork belly"
    # works with the app's own rules
    vegan = {"name": "Mira", "diet": "vegan", "allergies": "Soy", "dislikes": ""}
    assert logic.blockers(r, [vegan]) == ["Mira is vegan", "Mira can't eat soy"]
