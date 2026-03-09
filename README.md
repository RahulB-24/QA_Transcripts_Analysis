# 🔍 Trust-Weighted Question Answering over Meeting Transcripts

A full-stack AI-powered system that lets users ask natural-language questions about multi-speaker meeting transcripts and receive answers **grounded in evidence**, weighted by **speaker reliability scores**.

Built on the [AMI Meeting Corpus](https://huggingface.co/datasets/edinburghcstr/ami) — a dataset of real multi-party meetings with speaker-labeled transcripts.

---

## ✨ Features

- **Meeting Selection** — Browse and select from available AMI meetings
- **Natural Language QA** — Ask any question about a meeting's discussion
- **Trust-Weighted Retrieval** — Evidence ranked by `semantic_similarity × speaker_trust`
- **Speaker Reliability Scores** — Per-speaker trust computed from behavioural analysis + contradiction detection
- **Grounded Answers** — Flan-T5 generates answers citing specific transcript segments
- **Evidence Cards** — Visual display of supporting quotes with speaker, timestamp, and trust score

---

## 🏗️ Architecture

```
User Question
     │
     ▼
┌──────────────────────────┐
│  Sentence-Transformer    │  ← encodes question into 384-dim vector
│  (all-MiniLM-L6-v2)      │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  FAISS Index Search      │  ← finds top-10 similar utterances
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  Trust Re-ranking        │  ← similarity × speaker trust score
│  (heuristic + BART-MNLI) │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  Flan-T5-base            │  ← generates answer from evidence
└──────────┬───────────────┘
           ▼
     Answer + Evidence
```

---

## 🧠 AI/ML Models

| Model | Purpose | Size |
|-------|---------|------|
| [`facebook/bart-large-mnli`](https://huggingface.co/facebook/bart-large-mnli) | Contradiction detection via NLI | ~1.6 GB |
| [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Utterance & query embeddings | ~80 MB |
| [`google/flan-t5-base`](https://huggingface.co/google/flan-t5-base) | Answer generation | ~990 MB |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **ML** | Transformers, Sentence-Transformers, FAISS, PyTorch, scikit-learn |
| **Frontend** | React 19, TypeScript, Vite 6, TailwindCSS v4 |
| **Dataset** | AMI Meeting Corpus (`edinburghcstr/ami`, `ihm` subset) |

---

## 📁 Project Structure

```
├── backend/
│   ├── api/server.py                    # FastAPI server (GET /meetings, POST /ask)
│   ├── data/dataset_loader.py           # AMI dataset streaming & caching
│   ├── preprocessing/conversation_builder.py  # Utterance grouping by meeting
│   ├── trust_model/
│   │   ├── speaker_features.py          # Behavioural feature extraction
│   │   ├── contradiction_detector.py    # NLI-based contradiction detection
│   │   └── trust_scorer.py              # Weighted trust formula
│   ├── retrieval/
│   │   ├── embedding_index.py           # FAISS index construction
│   │   └── retriever.py                 # Trust-weighted semantic retrieval
│   ├── qa/answer_generator.py           # Flan-T5 answer generation
│   ├── pipeline/pipeline.py             # End-to-end orchestration
│   ├── storage/                         # Cached data (auto-generated)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                      # Root component
│   │   ├── components/
│   │   │   ├── MeetingSelector.tsx       # Meeting dropdown
│   │   │   ├── QuestionBox.tsx           # Question input
│   │   │   ├── AnswerPanel.tsx           # Answer display
│   │   │   └── EvidenceCard.tsx          # Evidence with trust bars
│   │   ├── services/api.ts              # API service layer
│   │   └── types/apiTypes.ts            # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
│
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Backend

```bash
cd backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows

pip install -r requirements.txt
uvicorn api.server:app --reload
```

> **Note:** First launch downloads ML models (~2.7 GB) and streams the AMI dataset. This takes 30–60 minutes. Subsequent launches use cached data and start in seconds.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 📡 API Endpoints

### `GET /meetings`
Returns a list of available meeting IDs.

### `POST /ask`

**Request:**
```json
{
  "meeting_id": "ES2003a",
  "question": "What decisions were made about the remote control design?"
}
```

**Response:**
```json
{
  "answer": "The team discussed using rubber buttons and a sleek design...",
  "evidence": [
    {
      "speaker": "MEE009",
      "text": "I think we should go with the ergonomic design",
      "timestamp": 245.3,
      "trust_score": 0.87
    }
  ]
}
```

---

## 🔬 Trust Scoring

Speaker trust is computed per-meeting using a weighted formula:

```
trust = consistency × 0.35
      + confidence × 0.25
      + low_contradiction × 0.25
      + stability × 0.15
```

| Component | Source |
|-----------|--------|
| **Consistency** | Inverse of self-correction frequency |
| **Confidence** | Lexical confidence minus hesitation penalty |
| **Low Contradiction** | 1 − contradiction ratio (via BART-MNLI NLI) |
| **Stability** | Statement count adjusted for interruptions |

---

## 📄 License

This project is for educational and research purposes.

---

## 🙏 Acknowledgements

- [AMI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/corpus/) — Edinburgh CSTR
- [Hugging Face](https://huggingface.co/) — Models & Datasets
- [FAISS](https://github.com/facebookresearch/faiss) — Facebook AI Similarity Search
