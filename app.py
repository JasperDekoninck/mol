from flask import Flask, render_template, request, jsonify
import csv
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(STATIC_DIR, "data")
OUTPUT_DIR = os.path.join(STATIC_DIR, "output")
MOLE_NAME = "De Mol"
DEFAULT_CSV = "data/test1.csv"
DEFAULT_BONUS = "data/extra.csv"


def resolve_csv_path(csv_param: str):
    if not csv_param:
        csv_param = "data/test1.csv"

    normalized = os.path.normpath(csv_param).lstrip(os.sep)
    if normalized.startswith("static" + os.sep):
        normalized = normalized[len("static") + 1 :]

    abs_path = os.path.join(STATIC_DIR, normalized)
    if not abs_path.startswith(STATIC_DIR + os.sep):
        return None, None

    if not os.path.isfile(abs_path):
        return None, None

    return abs_path, normalized


def load_bonus_map(csv_path: str):
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        field_map = {name.lower(): name for name in (reader.fieldnames or [])}
        name_key = None
        bonus_key = None
        for key in ("naam", "name", "voornaam"):
            if key in field_map:
                name_key = field_map[key]
                break
        if "bonus" in field_map:
            bonus_key = field_map["bonus"]

        if not name_key or not bonus_key:
            raise ValueError("Bonus CSV must include name and bonus columns.")

        bonuses = {}
        for row in reader:
            raw_name = (row.get(name_key) or "").strip()
            if not raw_name:
                continue
            raw_bonus = row.get(bonus_key, "0")
            try:
                bonus_value = (float(raw_bonus) / 100.0) if raw_bonus else 0.0
            except ValueError:
                bonus_value = 0.0
            bonuses[raw_name.lower()] = bonus_value

    return bonuses


def load_rankings(csv_path: str, bonus_path: str = None):
    bonuses = {}
    if bonus_path:
        bonuses = load_bonus_map(bonus_path)

    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        player_columns = [
            name for name in fieldnames if name not in ("Timestamp", "Voornaam")
        ]

        mole_column = None
        for name in player_columns:
            if name == MOLE_NAME:
                mole_column = name
                break

        if not mole_column:
            raise ValueError("Mole column not found.")

        entries = []
        for index, row in enumerate(reader):
            player_name = (row.get("Voornaam") or "").strip()
            total = 0.0
            scores = {}
            for col in player_columns:
                raw_value = row.get(col, "0")
                try:
                    value = float(raw_value) if raw_value else 0.0
                except ValueError:
                    value = 0.0
                scores[col] = value
                total += value

            mole_score = scores.get(mole_column, 0.0)
            mole_probability = mole_score / total if total > 0 else 0.0
            if bonuses:
                mole_probability += bonuses.get(player_name.lower(), 0.0)
            entries.append(
                {
                    "name": player_name,
                    "mole_probability": mole_probability,
                    "index": index,
                }
            )

    ranked = sorted(entries, key=lambda item: (-item["mole_probability"], item["index"]))
    return ranked


def write_rankings_csv(ranked, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Rank", "Name", "Points"])
        for rank, item in enumerate(ranked, start=1):
            writer.writerow([rank, item["name"], item["mole_probability"]])


@app.route("/", methods=["GET"])
def index():
    csv_param = request.args.get("csv", DEFAULT_CSV)
    extra_param = request.args.get("extra", DEFAULT_BONUS)
    _, normalized = resolve_csv_path(csv_param)
    _, extra_normalized = resolve_csv_path(extra_param)
    error = request.args.get("error")
    return render_template(
        "index.html",
        csv_param=normalized or csv_param,
        extra_param=extra_normalized or extra_param,
        error=error,
    )


@app.route("/check", methods=["POST"])
def check_name():
    name = (request.form.get("name") or "").strip()
    csv_param = request.form.get("csv", DEFAULT_CSV)
    extra_param = request.form.get("extra", DEFAULT_BONUS)
    csv_path, normalized = resolve_csv_path(csv_param)
    extra_path, _ = resolve_csv_path(extra_param)

    if not name:
        return "", 204

    ranked = load_rankings(csv_path, extra_path)
    name_lookup = {item["name"].lower(): item for item in ranked if item["name"]}
    if name.lower() not in name_lookup:
        return "", 204

    bottom_three = {item["name"].lower() for item in ranked[-3:] if item["name"]}
    color = "red" if name.lower() in bottom_three else "green"

    return jsonify({"color": color})


def generate_rankings_csv():
    csv_path, _ = resolve_csv_path(DEFAULT_CSV)
    extra_path, _ = resolve_csv_path(DEFAULT_BONUS)
    ranked = load_rankings(csv_path, extra_path)
    output_path = os.path.join(OUTPUT_DIR, "rankings.csv")
    write_rankings_csv(ranked, output_path)


generate_rankings_csv()

if __name__ == "__main__":
    app.run(debug=True)
