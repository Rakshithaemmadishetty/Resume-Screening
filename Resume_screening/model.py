import re
import pdfplumber
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------- TEXT EXTRACTION ----------
def extract_text(file):
    if file.filename.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
        return text

    elif file.filename.endswith(".docx"):
        doc = docx.Document(file)
        return " ".join(p.text for p in doc.paragraphs)

    return ""


# ---------- CLEAN TEXT ----------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------- KEYWORD EXTRACTION FROM JOB DESCRIPTION ----------
def extract_keywords(job_desc):
    words = clean_text(job_desc).split()
    keywords = set(words)
    return keywords


# ---------- RESUME RANKING ----------
def rank_resumes(job_desc, resumes, names):
    # Clean job description & resumes
    cleaned_job = clean_text(job_desc)
    cleaned_resumes = [clean_text(r) for r in resumes]

    # TF-IDF with phrase support
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_df=0.9
    )

    corpus = [cleaned_job] + cleaned_resumes
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Cosine similarity
    cosine_scores = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:]
    )[0]

    # Keyword-based boost
    job_keywords = extract_keywords(job_desc)

    final_scores = []
    for i, resume_text in enumerate(cleaned_resumes):
        keyword_matches = sum(
            1 for word in job_keywords if word in resume_text
        )

        tfidf_score = cosine_scores[i] * 100
        boost = min(keyword_matches * 0.5, 15)  # max 15% boost

        final_score = int(min(tfidf_score + boost, 100))
        final_scores.append(final_score)

    # Rank resumes
    ranked = sorted(
        zip(names, final_scores),
        key=lambda x: x[1],
        reverse=True
    )

    return ranked
