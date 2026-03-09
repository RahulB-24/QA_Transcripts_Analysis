# Trust-Weighted Question Answering over Meeting Transcripts

A production-quality research prototype that enables users to select meetings from the AMI meeting corpus, ask natural-language questions, and receive answers grounded in transcript evidence with per-speaker trust scores.

## Architecture

| Layer | Module | Description |
|-------|--------|-------------|
| Data ingestion | `data/dataset_loader.py` | Loads AMI dataset from Hugging Face |
| Preprocessing | `preprocessing/conversation_builder.py` | Groups & sorts utterances into conversations |
| Speaker features | `trust_model/speaker_features.py` | Extracts behavioural features per speaker |
| Contradiction detection | `trust_model/contradiction_detector.py` | NLI-based self-contradiction detection |
| Trust scoring | `trust_model/trust_scorer.py` | Weighted trust formula per speaker |
| Retrieval | `retrieval/embedding_index.py`, `retrieval/retriever.py` | FAISS semantic search + trust re-ranking |
| QA | `qa/answer_generator.py` | Flan-T5 answer generation |
| API | `api/server.py` | FastAPI REST server |
| Frontend | `../frontend/` | React + TypeScript + TailwindCSS |

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

## Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server (first run downloads models & dataset — may take several minutes)
uvicorn api.server:app --reload
```

The API will be available at `http://localhost:8000`.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/meetings` | List available meeting IDs |
| POST | `/ask` | Ask a question about a meeting |

**POST /ask** request body:

```json
{
  "meeting_id": "ES2002a",
  "question": "What was the main discussion topic?"
}
```

**Response:**

```json
{
  "answer": "The main discussion was about ...",
  "evidence": [
    {
      "speaker": "MEE070",
      "text": "I think we should focus on...",
      "timestamp": 120.5,
      "trust_score": 0.82
    }
  ]
}
```

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Demo Experience

1. Open the web interface at `http://localhost:5173`
2. Select a meeting from the dropdown
3. Type a question about the meeting
4. View the generated answer with supporting evidence and speaker trust scores

## Models Used

| Model | Purpose | Size |
|-------|---------|------|
| `facebook/bart-large-mnli` | Contradiction detection (NLI) | ~1.6 GB |
| `sentence-transformers/all-MiniLM-L6-v2` | Utterance embeddings | ~80 MB |
| `google/flan-t5-base` | Answer generation | ~990 MB |

## Dataset

**AMI Meeting Corpus** (`edinburghcstr/ami`, subset `ihm`) — a multi-party meeting dataset with speaker-labeled transcripts.
