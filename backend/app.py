from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from warfarin_logic import (
    WarfarinCalculatorError,
    calculate,
    parse_genetic_csv,
    parse_manual_genetic,
    self_test,
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # PGx CSV is intentionally tiny.


def as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "calculator": "warfarin", "version": "1.3.1"}


@app.post("/api/calculate")
def api_calculate():
    try:
        target_inr = request.form.get("target_inr", "2.0-3.0").strip()
        if target_inr and target_inr not in {"2.0-3.0", "2-3", "2.0–3.0"}:
            raise WarfarinCalculatorError(
                "This calculator is not validated for the selected INR target. "
                "Use an indication-specific clinical dosing protocol."
            )

        age = int(request.form["age"])
        height_cm = float(request.form["height_cm"])
        weight_kg = float(request.form["weight_kg"])
        population = request.form["population"].strip()
        african_context = (
            request.form.get("african_context")
            or request.form.get("rs127_context")
            or "unknown"
        ).strip() or "unknown"
        amiodarone = as_bool(request.form.get("amiodarone", "false"))
        enzyme_inducer = as_bool(request.form.get("enzyme_inducer", "false"))

        genetic = None
        uploaded = request.files.get("genetic_file")
        manual_requested = as_bool(request.form.get("manual_pgx", "false"))

        if uploaded and uploaded.filename and manual_requested:
            raise WarfarinCalculatorError("Use either an Xcode PGx file or manual PGx entry, not both.")

        if uploaded and uploaded.filename:
            genetic = parse_genetic_csv(uploaded.read())
        elif manual_requested:
            genetic = parse_manual_genetic(
                cyp2c9_allele1=request.form.get("cyp2c9_allele1", ""),
                cyp2c9_allele2=request.form.get("cyp2c9_allele2", ""),
                expanded_tested=as_bool(request.form.get("expanded_tested", "false")),
                vkorc1=request.form.get("vkorc1", ""),
                cyp4f2=request.form.get("cyp4f2", ""),
                rs12777823=request.form.get("rs12777823", ""),
            )

        result = calculate(
            age=age,
            height_cm=height_cm,
            weight_kg=weight_kg,
            population=population,
            african_context=african_context,
            amiodarone=amiodarone,
            enzyme_inducer=enzyme_inducer,
            genetic=genetic,
        )
        return jsonify(result)

    except KeyError as exc:
        return jsonify({"error": f"Missing field: {exc.args[0]}"}), 400
    except (ValueError, WarfarinCalculatorError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Unexpected calculator error")
        return jsonify({"error": "The calculation could not be completed."}), 500


import os


if __name__ == "__main__":
    self_test()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
