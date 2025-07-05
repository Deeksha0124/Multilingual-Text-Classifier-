from flask import Flask, request, jsonify, render_template, send_file
from predict_reviews import process_review, export_results, collection
from collections import Counter
import json
import csv
import time
from io import StringIO

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    text = request.json.get("review", "").strip()
    if not text:
        return jsonify({"error": "Empty review"}), 400

    row = {
        "review_id": "UI_001",
        "product_id": "UI_PROD",
        "reviewer_id": "UI_USER",
        "stars": None,
        "review_body": text,
        "review_title": "N/A"
    }

    result = process_review(row)
    collection.insert_one({
        "detected_language": result['detected_language'],
        "translated_text": result['translated_text'],
        "product_category": result['product_category'],
        "predicted_sentiment": result['predicted_sentiment'],
        "sentiment_scores": result['sentiment_scores'],
        "emoji": result['emoji'],
        "influential_keywords": result['influential_keywords'],
        "suggested_star_rating": result['stars'],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify(result)

@app.route("/export")
def export():
    fmt = request.args.get("format", "csv")
    data = list(collection.find({}, {"_id": 0}))
    if not data:
        return "No data available", 404

    timestamp = time.strftime("%d%m%Y_%H%M%S")
    if fmt == "json":
        response = app.response_class(
            response=json.dumps(data, indent=2),
            mimetype="application/json"
        )
        response.headers["Content-Disposition"] = f"attachment; filename=export_{timestamp}.json"
        return response
    else:
        # 🔧 Get all unique field names from all records
        fieldnames = sorted({key for doc in data for key in doc})
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
        response = app.response_class(
            response=output.getvalue(),
            mimetype="text/csv"
        )
        response.headers["Content-Disposition"] = f"attachment; filename=export_{timestamp}.csv"
        return response


@app.route("/stats")
def stats():
    data = list(collection.find({}, {"_id": 0}))
    sentiments = [d["predicted_sentiment"] for d in data]
    langs = [d["detected_language"] for d in data]
    return jsonify({
        "sentiment_counts": dict(Counter(sentiments)),
        "language_counts": dict(Counter(langs))
    })

from flask import send_file

@app.route("/analysis_image")
def analysis_image():
    return send_file(
        r"E:/BNMIT/6th sem/Multilingual text classifier/model/dataset_analysis.png",
        mimetype="image/png",
        as_attachment=False,
        download_name="dataset_analysis.png"
    )

if __name__ == "__main__":
    app.run(debug=True)
