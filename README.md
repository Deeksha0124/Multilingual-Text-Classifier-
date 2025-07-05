# 🌍 Multilingual Text Classifier

With so much text data being generated in different languages on social media, emails, and customer reviews, it becomes difficult to process, store, and analyse it efficiently. Traditional methods struggle with handling large amounts of multilingual data, making it slow and ineffective. So this project focuses on creating a web-based application to analyze multilingual customer reviews with automatic language detection, translation, sentiment analysis, and category prediction.

## Features

- Detects the language of the input text 
- Translates non-English reviews to English before processing
- Predicts sentiment (Positive, Negative, Neutral) with confidence scores
- Suggests relevant product categories (e.g., fashion, electronics)
- Allows voice input for quick review submission 🎤
- Exports predictions as **CSV** or **JSON**
- Displays interactive charts for language and sentiment distribution

## Tech Stack

- **Frontend**: HTML, CSS , JavaScript, Chart.js
- **Backend**: Python (Flask)
- **NLP Models**: Hugging Face Transformers (e.g., BERT, MarianMT), custom-trained models
- **Database**: MongoDB (to store predictions and feedback)
- **Voice Recognition**: Web Speech API
- **Visualization**: Matplotlib, Seaborn

## Requirements

- Python 3.8+
- Node.js (for serving frontend optionally)
- MongoDB (local or Atlas)

  **Python Packages:**
  ```bash
  flask
  transformers
  torch
  googletrans==4.0.0rc1
  pymongo
  matplotlib
  seaborn

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/Deeksha0124/Multilingual-Text-Classifier-.git
cd multilingual-text-classifier
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure MongoDB**
- Start MongoDB server locally, or set `MONGO_URI` in `app.py` for cloud MongoDB Atlas.

5. **Run the app**
```bash
python app.py
```
The app will be live at `http://127.0.0.1:5000`


