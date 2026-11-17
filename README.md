# WG Organizer (simplified draft)

A Streamlit app for a flat share: split costs fairly, organise chores and shopping, and find dishes everyone at home can eat. It learns from your ratings what each flatmate likes.

## Run it

You need Python 3.10 or newer.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Tests for the money and cooking rules: `python -m pytest`

### More recipes from Kaggle (optional)

The app ships with 45 hand-written recipes plus 3000 main-course recipes from Kaggle in `recipes_kaggle.csv`
(already converted, nothing to run). To rebuild that file, e.g. with more recipes, from the Kaggle dataset
[Recipes Dataset: 64k Dishes](https://www.kaggle.com/datasets/prashantsingh001/recipes-dataset-64k-dishes) (CC0), run once:

```bash
python import_recipes.py            # 3000 main-course recipes (fast enough for the app)
python import_recipes.py --max 0    # all main-course recipes
python import_recipes.py --csv path/to/1_Recipe_csv.csv   # if you downloaded the file yourself
```

This downloads the data with `kagglehub`, converts it to the app's format and saves `recipes_kaggle.csv`,
which the Cooking page loads next to `recipes.csv`. The dataset has no diet, allergens, cuisine or cooking time,
so `import_recipes.py` estimates them with keyword rules (e.g. "chicken" → meat, "flour" → gluten).
These are estimates: check the ingredients if someone has a serious allergy.

All files sit in one folder, so they can be uploaded to GitHub in one go. The only exception is the colour theme
(HSG green): Streamlit only reads it from `.streamlit/config.toml`, so that one file needs its folder.

## How it covers the requirements

| Requirement | Where |
|---|---|
| Data via API / database | ECB exchange rates via the Frankfurter API (`fx.py`), SQLite database (`db.py`), recipe data (`recipes.csv`, optionally Kaggle via `import_recipes.py`) |
| Visualisation | Fair Split: spending per month and category, balances per person |
| User interaction | Every page: forms, filters, ratings, ticking off chores and items |
| Machine learning | `ml.py`: one ridge regression per flatmate predicts ratings from cuisine, diet, tags and cooking time |

## Files

| File | Contents |
|---|---|
| `app.py` | Start page: first setup, "who's home today", navigation |
| `split.py` | Fair Split: expenses, charts, who pays whom |
| `house.py` | Cleaning rota and shopping list |
| `cooking.py` | Suggestions, ratings, what the model learned |
| `flatmates.py` | Food preferences, adding and removing flatmates |
| `logic.py` | Rules as plain functions: balances, settling up, rota, diet/allergy/dislike checks |
| `ml.py` | Machine learning |
| `fx.py` | Exchange rates |
| `db.py` | Database tables and helpers |
| `recipes.csv` | 45 recipes |
| `import_recipes.py` | Imports and converts the Kaggle recipes into `recipes_kaggle.csv` |
| `test_logic.py` | Tests for `logic.py` |
| `test_import.py` | Tests for the keyword rules in `import_recipes.py` |

Data is stored in `wg.sqlite` next to `app.py`. There is no login.

## Use of AI

This draft was generated with Claude (Anthropic) in November 2026, based on an earlier vibe-coded version. Each file is marked accordingly.
