import os
import re
import csv
import json
import time
import torch
import random
import string
import speech_recognition as sr
import torch.nn.functional as F
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from langdetect import detect
from bs4 import BeautifulSoup
from unidecode import unidecode
from pymongo import MongoClient
from deep_translator import GoogleTranslator
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import expit
from sklearn.metrics import accuracy_score
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType
from pyspark.sql.functions import udf
from multiprocessing import Pool
from pyspark import RDD


# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["sentiment_db"]
collection = db["review_predictions"]



# Model Loaders
tokenizer = AutoTokenizer.from_pretrained(r"E:/BNMIT/6th sem/Multilingual text classifier/model/models/Sentiment_Model_10000/models/sentiment_model/checkpoint-1875", local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained(r"E:/BNMIT/6th sem/Multilingual text classifier/model/models/Sentiment_Model_10000/models/sentiment_model/checkpoint-1875")
model.eval()

topic_tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/tweet-topic-base-multilingual")
topic_model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/tweet-topic-base-multilingual")
topic_model.eval()
topic_id2label = topic_model.config.id2label




# Mappings
label_map = {0: "Negative", 1: "Neutral", 2: "Positive"}
emoji_map = {"Negative": "😠", "Neutral": "😐", "Positive": "😊"}




# Cleaning utilities
def clean_review(text):
    text = re.sub(r"http\S+", "", text)
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r"[^\w\s]", "", text)
    text = unidecode(text)
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    return text.strip()



# Translation
def translate_text(text, source_lang):
    if source_lang != "en":
        try:
            return  GoogleTranslator(source=source_lang, target="en").translate(text)
        except:
            print("\n Fallback: Using original text")
    return text




# Voice Input
def get_voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Speak now...")
        audio = r.listen(source)
        try:
            return r.recognize_google(audio)
        except Exception as e:
            print(f"\n Could not understand audio: {e}")
            return ""




# Keyword extraction
def extract_keywords(text, top_n=3):
    words = [w for w in text.split() if len(w) > 3]
    scored = {w: random.random() for w in words}
    return [k for k, _ in sorted(scored.items(), key=lambda x: x[1], reverse=True)[:top_n]]



# Topic detection
def detect_category(text, threshold=0.5):
    inputs = topic_tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        probs = expit(topic_model(**inputs).logits[0].numpy())
    idx = int(probs.argmax())
    conf = probs[idx]
    return topic_id2label[idx] if conf >= threshold else f"Uncertain  — Best guess: {topic_id2label[idx]}"



# Sentiment classification
def classify_review(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        probs = F.softmax(model(**inputs).logits, dim=-1).squeeze()

    top_idx = torch.argmax(probs).item()
    sentiment = label_map[top_idx]

    
    if max(probs) - sorted(probs, reverse=True)[1] < 0.1: 
        sentiment = "Neutral" 

    if sentiment == "Positive":
        suggested_rating = 5  
    elif sentiment == "Neutral":
        suggested_rating = 3
    else:  
        suggested_rating = 1 

    return suggested_rating



# Check for duplicates
def is_duplicate(text):
    return collection.find_one({"translated_text": text}) is not None


# Export tool
def export_results(format="csv"):
    data = list(collection.find({}, {"_id": 0}))
    if not data:
        print("\n No data to export.")
        return
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    if format == "json":
        with open(f"export_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        with open(f"export_{timestamp}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    print(f"\n Exported {len(data)} entries to {format.upper()} file.")




# Dataset analyzer
def analyze_dataset():
    data = list(collection.find({}, {"_id": 0}))
    if not data:
        print("No data found.")
        return

    # Prepare output directory
    output_dir = r"E:/BNMIT/6th sem/Multilingual text classifier/model"
    os.makedirs(output_dir, exist_ok=True)

    # Data
    langs = [d["detected_language"] for d in data]
    sentiments = [d["predicted_sentiment"] for d in data]

    # Plotting
    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 5))

    # Language Distribution
    plt.subplot(1, 2, 1)
    sns.countplot(x=langs)
    plt.title("Language Distribution")
    plt.xticks(rotation=45)

    # Sentiment Distribution
    plt.subplot(1, 2, 2)
    sns.countplot(x=sentiments)
    plt.title("Sentiment Distribution")

    plt.tight_layout()

    # Save figure
    save_path = os.path.join(output_dir, "dataset_analysis.png")
    plt.savefig(save_path)
    print(f"Analysis saved to: {save_path}")

    plt.close()


# Function to process each row (this would be run on each partition in parallel)
def process_review(row):
    text = clean_review(str(row["review_body"]))
    try:
        lang = detect(text)
    except:
        lang = "unknown"
    translated = translate_text(text, lang)
    
    # Sentiment classification
    inputs = tokenizer(translated, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        probs = F.softmax(model(**inputs).logits, dim=-1).squeeze()

    pred_idx = torch.argmax(probs).item()
    predicted = label_map[pred_idx]
    confidence = probs[pred_idx].item()

    # Finer-grained star rating logic
    if predicted == "Positive":
        if confidence >= 0.85:
            rating = 5.0
        elif confidence >= 0.65:
            rating = 4.5
        else:
            rating = 4.0
    elif predicted == "Neutral":
        if confidence >= 0.80:
            rating = 3.5
        elif confidence >= 0.65:
            rating = 3.0
        else:
            rating = 2.5
    else:  # Negative
        if confidence >= 0.75:
            rating = 2.0
        elif confidence >= 0.60:
            rating = 1.5
        else:
            rating = 1.0


    return {
        "review_id": row["review_id"],
        "product_id": row["product_id"],
        "reviewer_id": row["reviewer_id"],
        "stars": rating,
        "review_body": row["review_body"],
        "review_title": row["review_title"],
        "detected_language": lang,
        "translated_text": translated,
        "product_category": detect_category(translated),
        "predicted_sentiment": predicted,
        "sentiment_scores": {label_map[i]: f"{probs[i].item()*100:.2f}%" for i in range(len(label_map))},
        "emoji": emoji_map[predicted],
        "influential_keywords": extract_keywords(translated)
    }




# Evaluate the model on the CSV with Spark
def evaluate_model_on_csv_with_spark(csv_path):
    if not os.path.exists(csv_path):
        print(f" CSV file not found at: {csv_path}")
        return

    spark = SparkSession.builder \
        .appName("MultilingualReviewSentimentEvaluation") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .conf.set("spark.executor.cores", "2") \
        .getOrCreate()

    try:
        
        df = spark.read.option("header", "true").option("inferSchema", "true").csv(csv_path)
        df = df.limit(10)  
      
        df = df.filter(df["review_body"].isNotNull())
        print(f"\n Loaded {df.count()} rows from: {csv_path}")

        process_review_udf = udf(process_review, StringType()) 

        df_with_sentiment = df.withColumn("processed_review", process_review_udf(df["review_body"]))
        results = df_with_sentiment.select("review_id", "derived_sentiment", "processed_review").collect()

        review_ids, true_labels, predicted_labels = zip(*[(row["review_id"], row["derived_sentiment"], row["processed_review"]["predicted_sentiment"]) for row in results])

        acc = accuracy_score(true_labels, predicted_labels)
        print(f"\n Model Accuracy on CSV: {acc:.2%}")

       
        print("\n Misclassified reviews:")
        for review_id, true, pred in zip(review_ids, true_labels, predicted_labels):
            if true != pred:
                print(f"   - Review ID {review_id}: true = {true}, predicted = {pred}")

    except Exception as e:
        print(f"\n Error during evaluation: {e}")

    finally:
        spark.stop()



if __name__ == "__main__":
#  Main Loop
    while True:
        print("\n Choose input mode: (1) Text (2) Voice (3) Export (4) Analyze (5) Exit ")
        choice = input("\n Your choice:  \n").strip()

        if choice == "5":
            break
        elif choice == "3":
            fmt = input("\n Export format (csv/json): ").strip().lower()
            export_results(fmt)
            continue
        elif choice == "4":
            analyze_dataset()
            continue
        

        if choice == "1":
            user_input = input("\n Enter your review: ").strip()
        elif choice == "2":
            user_input = get_voice_input()
        else:
            print("\n Invalid choice.")
            continue

        if not user_input:
            print("\n Empty input.")
            continue




     # Process review in parallel
    print("\n Processing your review...")
    processed_review = process_review({
    "review_id": "N/A",
    "product_id": "N/A",
    "reviewer_id": "N/A",
    "stars": None,
    "review_body": user_input,
    "review_title": "N/A"
})

    # Process the results from parallelization
    if processed_review:
        # Output the results
        print("\n Results:")
        print(f"\n Language: {processed_review['detected_language']}")
        print(f"\n Translated: {processed_review['translated_text']}")
        print(f"\n Category: {processed_review['product_category']}")
        print(f"\n Sentiment: {processed_review['predicted_sentiment']} {processed_review['emoji']}")
        print(f"\n Influential_keywords: {', '.join(processed_review['influential_keywords'])}")
        print(f"\n Suggested Star rating: {processed_review['stars']}")
        print(f"\n Scores: {processed_review['sentiment_scores']}")

        feedback = input("\n Is the prediction accurate? (y/n): ").strip().lower()

        doc = {
            "detected_language": processed_review['detected_language'],
            "translated_text": processed_review['translated_text'],
            "product_category": processed_review['product_category'],
            "predicted_sentiment": processed_review['predicted_sentiment'],
            "sentiment_scores": processed_review['sentiment_scores'],
            "emoji": processed_review['emoji'],
            "influential_keywords": processed_review['influential_keywords'],
            "suggested_star_rating": processed_review['stars'],
            "human_feedback": feedback,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            collection.insert_one(doc)
            print("\n Saved to MongoDB.\n")
        except Exception as e:
            print(f"\n MongoDB Error: {e}")
