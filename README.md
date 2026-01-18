# Document Chatbot with CMS Integration

A Retrieval-Augmented Generation (RAG) chatbot that answers questions based on uploaded documents and CMS content using vector search.

## Features

- 📄 Upload and analyze PDF, DOCX, and CSV files
- 🔍 Semantic search using vector embeddings
- 💬 Interactive chat interface with source citations
- 🗃️ CMS content ingestion (simulated with text input)
- 🎨 Modern, responsive UI with dark mode
- 🔗 Qdrant Cloud vector database integration

## Tech Stack

### Backend
- **FastAPI** - Python web framework
- **Sentence Transformers** - Local embedding generation
- **Qdrant Cloud** - Vector database
- **PyPDF, python-docx, pandas** - Document parsing

### Frontend
- **HTML5, CSS3, JavaScript** - Frontend interface
- **Font Awesome** - Icons
- **Google Fonts** - Typography

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Node.js (optional, for serving frontend)
- Qdrant Cloud account (free tier)

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (Python 3.12)
py -3.12 -m venv .venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Copy the example file
cp .env.example .env

# Edit .env with your credentials:
# - QDRANT_URL: From Qdrant Cloud dashboard
# - QDRANT_API_KEY: From Qdrant Cloud dashboard
# - OPENAI_API_KEY: Optional, for enhanced answer generation

# Run the backend server
uvicorn app:app --reload --host 0.0.0.0 --port 8000