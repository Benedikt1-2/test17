"""Import extra recipes from Kaggle ("Recipes Dataset: 64k Dishes", CC0) into the app's recipe format.

Run once:  python import_recipes.py          (default: 3000 recipes)
           python import_recipes.py --max 0  (all main-course recipes)

Writes recipes_kaggle.csv. The Cooking page loads it next to recipes.csv automatically.

The Kaggle data only has title, category, ingredients and directions. Everything else the app
needs is derived here with simple keyword rules, so it is an estimate, not a fact:
- diet:      meat / pesce / veg / vegan, from meat, fish and animal-product words in the ingredients
- allergens: the 8 allergens the app knows, from ingredient words
- cuisine:   from words in the title and category, otherwise 'american' (the source site is American)
- minutes:   the times mentioned in the directions added up, otherwise a guess from the number of steps
- tags:      quick, spicy, soup, pasta, ... from title, category and time
"""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import argparse
import glob
import json
import os
import re

import pandas as pd

DATASET = "prashantsingh001/recipes-dataset-64k-dishes"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes_kaggle.csv")


def has(text: str, word_list) -> bool:
    """True if one of the words appears as a whole word (plural allowed) in text."""
    return any(re.search(rf"\b{re.escape(w)}(s|es)?\b", text) for w in word_list)


# ---------- diet ----------
MEAT = ["beef", "pork", "chicken", "turkey", "lamb", "veal", "duck", "goose", "bacon", "ham", "sausage",
        "steak", "prosciutto", "pancetta", "salami", "pepperoni", "chorizo", "hot dog", "meatball", "venison",
        "bratwurst", "kielbasa", "gelatin", "lard", "ground meat", "rib", "brisket", "veal", "mince"]
FISH = ["fish", "salmon", "tuna", "cod", "tilapia", "halibut", "trout", "sardine", "anchovy", "anchovies",
        "mackerel", "haddock", "catfish", "snapper", "swordfish", "bass", "worcestershire", "shrimp", "prawn", "crab",
        "lobster", "scallop", "clam", "mussel", "oyster", "squid", "calamari", "crawfish", "seafood"]
ANIMAL = ["egg", "milk", "butter", "cheese", "cream", "yogurt", "yoghurt", "honey", "mayonnaise", "mayo",
          "ghee", "parmesan", "mozzarella", "ricotta", "feta", "cheddar", "whey", "buttermilk", "custard"]
# plant versions that contain an animal word, removed before checking
PLANT_LOOKALIKES = ["eggplant", "butternut", "peanut butter", "almond butter", "cashew butter", "apple butter",
                    "nut butter", "cocoa butter", "coconut milk", "coconut cream", "almond milk", "oat milk",
                    "soy milk", "rice milk", "cream of tartar", "vegan butter", "vegan cheese", "vegan mayonnaise",
                    "egg-free", "dairy-free"]
NOT_REALLY_MEAT = ["vegetable broth", "vegetable stock", "chicken-of-the-woods"]


def clean(ingredients: str) -> str:
    text = ingredients.lower()
    for phrase in PLANT_LOOKALIKES + NOT_REALLY_MEAT:
        text = text.replace(phrase, " ")
    return text


def diet_of(ingredients: str) -> str:
    text = clean(ingredients)
    if has(text, MEAT):
        return "meat"
    if has(text, FISH):
        return "pesce"
    if has(text, ANIMAL):
        return "veg"
    return "vegan"


# ---------- allergens (same names as on the Flatmates page) ----------
ALLERGEN_WORDS = {
    "Gluten": ["flour", "bread", "breadcrumb", "panko", "pasta", "spaghetti", "noodle", "macaroni", "penne",
               "lasagna", "tortilla", "pita", "bun", "roll", "couscous", "bulgur", "barley", "rye", "wheat",
               "cracker", "crouton", "biscuit", "dough", "pastry", "phyllo", "filo", "pizza", "empanada", "wonton",
               "wrapper", "pretzel", "bagel", "croissant", "english muffin", "dumpling", "beer", "soy sauce", "seitan"],
    "Lactose": ["milk", "butter", "cheese", "cream", "yogurt", "yoghurt", "parmesan", "mozzarella", "ricotta",
                "feta", "cheddar", "buttermilk", "ghee", "whey", "custard", "half-and-half"],
    "Egg": ["egg", "mayonnaise", "mayo"],
    "Nuts": ["almond", "walnut", "pecan", "cashew", "hazelnut", "pistachio", "peanut", "macadamia", "pine nut",
             "nut"],
    "Soy": ["soy", "soya", "tofu", "tempeh", "edamame", "miso", "tamari"],
    "Fish": ["fish", "salmon", "tuna", "cod", "tilapia", "halibut", "trout", "sardine", "anchovy", "anchovies",
             "mackerel", "haddock", "catfish", "snapper", "swordfish", "bass", "fish sauce", "worcestershire"],
    "Shellfish": ["shrimp", "prawn", "crab", "lobster", "scallop", "clam", "mussel", "oyster", "squid",
                  "calamari", "crawfish"],
    "Sesame": ["sesame", "tahini"],
}


def allergens_of(ingredients: str) -> str:
    text = clean(ingredients)
    return ",".join(a for a, words in ALLERGEN_WORDS.items() if has(text, words))


# ---------- cuisine (same names as on the Flatmates page) ----------
CUISINE_WORDS = {
    "italian": ["italian", "pasta", "spaghetti", "lasagna", "risotto", "pizza", "gnocchi", "parmigiana",
                "carbonara", "pesto", "marinara", "alfredo", "bruschetta", "ravioli", "tortellini", "penne"],
    "mexican": ["mexican", "taco", "burrito", "enchilada", "quesadilla", "fajita", "salsa", "tamale",
                "chili", "nacho", "tex-mex", "chimichanga", "pozole", "carnitas", "tostada"],
    "indian": ["indian", "curry", "masala", "tikka", "tandoori", "dal", "dhal", "biryani", "korma", "paneer",
               "naan", "samosa", "vindaloo", "chana"],
    "asian": ["asian", "chinese", "japanese", "korean", "thai", "vietnamese", "filipino", "stir-fry", "stir fry",
              "teriyaki", "sushi", "ramen", "pho", "pad thai", "fried rice", "lo mein", "dumpling", "wok",
              "kimchi", "bibimbap", "soba", "udon", "miso", "gochujang", "szechuan", "sichuan", "kung pao", "satay"],
    "middle eastern": ["middle eastern", "lebanese", "turkish", "persian", "israeli", "falafel", "hummus",
                       "shawarma", "kebab", "kabob", "tabbouleh", "shakshuka", "za'atar"],
    "mediterranean": ["mediterranean", "greek", "spanish", "paella", "gyro", "souvlaki", "tzatziki",
                      "moussaka", "spanakopita", "tapas"],
    "french": ["french", "provencal", "ratatouille", "quiche", "coq au vin", "bourguignon", "gratin",
               "crepe", "cassoulet", "nicoise", "bouillabaisse"],
    "german": ["german", "austrian", "schnitzel", "sauerkraut", "spaetzle", "bratwurst", "strudel", "goulash"],
    "african": ["african", "moroccan", "ethiopian", "nigerian", "tagine", "jollof", "harissa", "egyptian"],
}


def cuisine_of(title: str, category: str) -> str:
    text = f"{title} {category}".lower()
    for cuisine, words in CUISINE_WORDS.items():
        if has(text, words):
            return cuisine
    return "american"


# ---------- cooking time ----------
TIME = re.compile(r"(\d+)(?:\s*(?:to|-|–)\s*(\d+))?\s*(minutes?|mins?|hours?|hrs?)\b", re.I)


def minutes_of(steps: list[str]) -> int:
    """Add up the times mentioned in the directions ('20 to 25 minutes' counts as 25)."""
    total = 0
    for step in steps:
        for low, high, unit in TIME.findall(step):
            value = int(high or low)
            total += value * 60 if unit.lower().startswith("h") else value
    if total == 0:
        total = 10 + 5 * len(steps)  # nothing mentioned: rough guess from the number of steps
    total += 10  # preparation (chopping, measuring) is hardly ever mentioned
    return int(min(max(round(total / 5) * 5, 10), 600))


# ---------- tags (only tags the app already uses) ----------
TAG_WORDS = {
    "soup": ["soup", "stew", "chowder", "bisque", "broth"],
    "pasta": ["pasta", "spaghetti", "noodle", "lasagna", "macaroni", "penne", "linguine", "fettuccine"],
    "curry": ["curry"],
    "wrap": ["wrap", "burrito", "tortilla"],
    "bowl": ["bowl"],
    "wok": ["stir-fry", "stir fry", "wok"],
    "tray bake": ["sheet pan", "sheet-pan", "tray bake"],
    "one pot": ["one-pot", "one pot", "slow cooker", "instant pot", "crockpot"],
    "one pan": ["one-pan", "one pan", "skillet"],
    "comfort": ["casserole", "mac and cheese", "pot pie", "meatloaf", "comfort"],
    "summer": ["salad", "grilled", "barbecue", "bbq"],
}
SPICY = ["chili", "chile", "jalapeno", "cayenne", "sriracha", "chipotle", "habanero", "hot sauce",
         "red pepper flakes", "gochujang", "harissa"]


def tags_of(title: str, category: str, ingredients: str, minutes: int) -> str:
    text = f"{title} {category}".lower()
    tags = [t for t, words in TAG_WORDS.items() if has(text, words)]
    if has(ingredients.lower(), SPICY):
        tags.append("spicy")
    if minutes <= 30:
        tags.append("quick")
    return ",".join(tags)


# ---------- the whole conversion ----------
# categories that are not a main dish for dinner at home
NOT_A_MEAL = ["dessert", "cake", "cookie", "pie", "candy", "candies", "frosting", "icing", "drink", "cocktail",
              "beverage", "smoothie", "punch", "coffee", "tea", "bread", "muffin", "scone", "pancake", "waffle",
              "brownie", "bar", "fudge", "jam", "jelly", "canning", "sauce", "dip", "dressing", "spice", "rub",
              "marinade", "frozen", "ice cream", "baby food", "pet"]
# sweets and snacks also hide in categories like 'Christmas' or 'Healthy Recipes', so check the title too
NOT_A_MEAL_TITLE = ["cookie", "cupcake", "cheesecake", "brownie", "blondie", "fudge", "muffin", "frosting", "icing",
                    "candy", "candies", "cocktail", "smoothie", "punch", "lemonade", "martini", "margarita", "bars",
                    "pudding", "scone", "cobbler", "crumble", "crisp", "ice cream", "sorbet", "dip", "jam", "jelly",
                    "granola", "biscotti", "macaroon", "meringue", "toffee", "mousse", "truffle", "pie", "tart",
                    "cinnamon roll", "party mix", "snack mix", "toast", "doughnut", "donut", "cake", "bread", "sauce", "dressing", "seasoning", "syrup"]
KEEP_TITLE = ["pot pie", "shepherd's pie", "cottage pie", "crab cake", "fish cake", "salmon cake", "potato cake",
              "meatloaf", "bread salad", "pasta sauce", "french toast", "avocado toast"]


def not_a_meal(title: str, category: str) -> bool:
    title = title.lower()
    if has(category, NOT_A_MEAL):
        return True
    return has(title, NOT_A_MEAL_TITLE) and not any(k in title for k in KEEP_TITLE)


def parse_list(value) -> list[str]:
    """The CSV stores ingredients and directions as JSON text: '["1 onion", "2 eggs"]'."""
    try:
        items = json.loads(value)
    except (TypeError, ValueError):
        return []
    # the app splits ingredients on '; ' and steps on ' | ', so those characters must not appear inside
    return [str(x).replace(";", ",").replace("|", "/").strip() for x in items if str(x).strip()]


def convert(raw: pd.DataFrame, max_recipes: int = 3000, seed: int = 42) -> pd.DataFrame:
    """Kaggle columns -> app columns (id, name, cuisine, diet, minutes, allergens, tags, ingredients, steps)."""
    df = raw.dropna(subset=["recipe_title", "ingredients", "directions"]).copy()
    category = (df["category"].fillna("") + " " + df["subcategory"].fillna("")).str.lower()
    meal = [not not_a_meal(t, c) for t, c in zip(df["recipe_title"].astype(str), category)]
    df = df[meal]
    df = df.drop_duplicates(subset="recipe_title")
    if max_recipes and len(df) > max_recipes:
        df = df.sample(max_recipes, random_state=seed)  # fixed seed: the same recipes every time

    rows = []
    for i, r in enumerate(df.itertuples()):
        ingredients, steps = parse_list(r.ingredients), parse_list(r.directions)
        if not ingredients or not steps:
            continue
        cat = f"{r.category} {r.subcategory}"
        text = " ".join(ingredients)
        minutes = minutes_of(steps)
        rows.append({
            "id": f"k{i}",
            "name": str(r.recipe_title).strip(),
            "cuisine": cuisine_of(r.recipe_title, cat),
            "diet": diet_of(text),
            "minutes": minutes,
            "allergens": allergens_of(text),
            "tags": tags_of(r.recipe_title, cat, text, minutes),
            "ingredients": "; ".join(ingredients),
            "steps": " | ".join(steps),
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max", type=int, default=3000, help="how many recipes to keep (0 = all)")
    parser.add_argument("--csv", help="use an already downloaded 1_Recipe_csv.csv instead of downloading")
    args = parser.parse_args()

    if args.csv:
        source = args.csv
    else:
        import kagglehub  # only needed for the download
        path = kagglehub.dataset_download(DATASET)
        print("Path to dataset files:", path)
        source = glob.glob(os.path.join(path, "**", "*.csv"), recursive=True)[0]

    recipes = convert(pd.read_csv(source), max_recipes=args.max)
    recipes.to_csv(OUT, index=False)
    print(f"Saved {len(recipes)} recipes to {OUT}")
    print("Diets:", recipes["diet"].value_counts().to_dict())
    print("Cuisines:", recipes["cuisine"].value_counts().to_dict())


if __name__ == "__main__":
    main()
