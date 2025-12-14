from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from newspaper import Article
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def extract_article_text(url: str) -> str:
    """
    Downloads and extracts clean text from a news article URL.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print("Error extracting article:", e)
        return ""
def extract_keywords(text: str, top_n: int = 20):
    """
    Extracts top N keywords using TF-IDF.
    """
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=2000)
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]

        # Get top N keyword indices
        top_indices = np.argsort(scores)[-top_n:][::-1]

        keywords = []
        for idx in top_indices:
            keywords.append({
                "word": feature_names[idx],
                "weight": float(scores[idx])
            })
        return keywords
    except Exception as e:
        print("Keyword extraction error:", e)
        return []


# ---------- Data Models ----------

class AnalyzeRequest(BaseModel):
    url: str


class WordItem(BaseModel):
    word: str
    weight: float


class AnalyzeResponse(BaseModel):
    words: List[WordItem]


# ---------- App Setup ----------

app = FastAPI(
    title="3D Word Cloud API",
    version="1.0.0",
)

# Frontend will run on one of these ports (we'll use 5173 for Vite later)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Routes ----------

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_article(payload: AnalyzeRequest):

    text = extract_article_text(payload.url)

    if not text:
        return AnalyzeResponse(words=[
            WordItem(word="error", weight=1.0),
            WordItem(word="failed_to_extract_text", weight=0.8)
        ])

    keywords = extract_keywords(text, top_n=25)

    # If nothing found, fallback
    if not keywords:
        keywords = [
            {"word": "no_keywords_found", "weight": 1.0}
        ]

    return AnalyzeResponse(words=[WordItem(**w) for w in keywords])

