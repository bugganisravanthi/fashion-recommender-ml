import os
import csv
from flask import Flask, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, "static", "images")
CSV_FILE = os.path.join(BASE_DIR, "fashion dataset.csv")


# Person category names and their matching image folders
PERSON_FOLDERS = {
    "women": ["women"],
    "men": ["men"],
    "girls": ["girls"],
    "boys": ["boys"],
    "baby boy": ["babyboy", "baby boy"],
    "baby girl": ["babygirl", "baby girl"],
    "children boys": ["children boys", "children_boys"],
    "children girls": ["children girls", "children_girls"],
    "teenagers boys": ["teenagers boys", "teenagers_boys"],
    "teenagers girls": ["teenagers girls", "teenagers_girls"],
    "grandparents": ["grandparents"]
}

CATEGORY_ALIASES = {
    "casual": ["casual"],
    "formal": ["formal"],
    "traditional": ["traditional", "ethnic"],
    "western": ["western"],
    "party": ["party"]
}


def get_images(person_category="", age="", category=""):
    images = []
    candidates = []

    if not os.path.isdir(IMAGE_FOLDER):
        return images

    person_category = person_category.strip().lower()
    category = category.strip().lower()
    age = age.strip().lower()

    allowed_folders = PERSON_FOLDERS.get(
        person_category, [person_category]
    )

    for root, dirs, files in os.walk(IMAGE_FOLDER):
        for filename in files:
            if not filename.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp", ".gif")
            ):
                continue

            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(
                full_path, IMAGE_FOLDER
            ).replace("\\", "/")

            parts = [
                part.lower().replace("_", " ").replace("-", " ")
                for part in relative_path.split("/")
            ]

            searchable = " ".join(parts)

            # Filter by person category using folder names
            if person_category and person_category not in (
                "all", "any", "select"
            ):
                folder_matches = any(
                    folder.lower() in parts[:-1]
                    for folder in allowed_folders
                )

                if not folder_matches:
                    continue

            # Filter by clothing category
            if category and category not in (
                "all", "any", "select"
            ):
                aliases = CATEGORY_ALIASES.get(
                    category, [category]
                )

                if not any(word in searchable for word in aliases):
                    continue

            candidates.append((relative_path, searchable))

    # Apply age only when age-labelled images are available.
    if age and age not in ("all", "any", "select"):
        age_number = "".join(ch for ch in age if ch.isdigit())

        if age_number:
            age_candidates = [
                item for item in candidates
                if age_number in item[1]
            ]

            if age_candidates:
                candidates = age_candidates

    for relative_path, searchable in candidates:
        images.append("images/" + relative_path)

    print("Selected person category:", person_category)
    print("Selected age:", age)
    print("Selected clothing category:", category)
    print("Images found:", len(images))

    return sorted(images)


def get_recommendations(occasion, budget, category):
    recommendations = []

    try:
        max_budget = float(budget)
    except (ValueError, TypeError):
        return recommendations

    if not os.path.isfile(CSV_FILE):
        print("CSV file not found:", CSV_FILE)
        return recommendations

    category = category.strip().lower()

    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                row_occasion = row.get("Occasion", "").strip()
                row_style = row.get("style", "").strip()
                row_budget = row.get("budget", "").strip()

                try:
                    item_budget = float(
                        row_budget.replace("₹", "").replace(",", "")
                    )
                except ValueError:
                    continue

                if row_occasion.lower() != occasion.strip().lower():
                    continue

                if category.lower() not in ("all", "any", "select"):
                    aliases = CATEGORY_ALIASES.get(
                        category.lower(), [category.lower()]
                    )
                    if not any(
                        word in row_style.lower() for word in aliases
                    ):
                        continue

                if item_budget <= max_budget:
                    recommendations.append(row)

    except Exception as error:
        print("CSV reading error:", error)

    return recommendations


@app.route("/", methods=["GET", "POST"])
def home():
    images = []
    recommendations = []

    selected_person = ""
    selected_age = ""
    selected_occasion = ""
    selected_budget = ""
    selected_category = ""

    if request.method == "POST":
        selected_person = request.form.get(
            "person_category", ""
        ).strip()

        selected_age = request.form.get("age", "").strip()
        selected_occasion = request.form.get("occasion", "").strip()
        selected_budget = request.form.get("budget", "").strip()
        selected_category = request.form.get(
            "category", ""
        ).strip()

        images = get_images(
            person_category=selected_person,
            age=selected_age,
            category=selected_category
        )

        recommendations = get_recommendations(
            selected_occasion,
            selected_budget,
            selected_category
        )

    return render_template(
        "index.html",
        images=images,
        recommendations=recommendations,
        selected_person=selected_person,
        selected_age=selected_age,
        selected_occasion=selected_occasion,
        selected_budget=selected_budget,
        selected_category=selected_category
    )


# Demo shop list: replace these with verified local shop details.
shops = [
    {
        "name": "Demo Fashion Store 1",
        "address": "Kondapur, Hyderabad",
        "phone": "Demo contact - not verified",
        "service_pincodes": ["500084", "500081"]
    },
    {
        "name": "Demo Fashion Store 2",
        "address": "Kukatpally, Hyderabad",
        "phone": "Demo contact - not verified",
        "service_pincodes": ["500072", "500085"]
    },
    {
        "name": "Demo Fashion Store 3",
        "address": "Begumpet, Hyderabad",
        "phone": "Demo contact - not verified",
        "service_pincodes": ["500016", "500003"]
    }
]


@app.route("/nearby-shops", methods=["GET", "POST"])
def nearby_shops():
    if request.method == "POST":
        pincode = request.form.get("pincode", "").strip()
    else:
        pincode = request.args.get("pincode", "").strip()

    if not pincode.isdigit() or len(pincode) != 6:
        return "Please enter a valid 6-digit PIN code."

    matching_shops = [
    shop for shop in shops
    if pincode in shop["service_pincodes"]
]

    return render_template(
    "nearby_shops.html",
    pincode=pincode,
    shops=matching_shops
)


@app.route("/select-shop", methods=["POST"])
def select_shop():
    shop_name = request.form.get("shop_name", "").strip()
    pincode = request.form.get("pincode", "").strip()

    selected_shop = next(
        (
            shop for shop in shops
            if shop["name"] == shop_name
            and pincode in shop["service_pincodes"]
        ),
        None
    )

    if selected_shop is None:
        return "Shop not found", 404

    return render_template(
        "shop_selected.html",
        shop_name=selected_shop["name"],
        address=selected_shop["address"],
        phone=selected_shop["phone"],
        pincode=pincode
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)