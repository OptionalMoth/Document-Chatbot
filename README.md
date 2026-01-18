# Document Chatbot with CMS Integration

A web-based chatbot that can answer questions based on uploaded documents (PDF, DOCX, CSV, TXT) and imported CMS content using a vector database (Qdrant).

## Features

- **File Upload**: Upload PDF, DOCX, CSV, and TXT files
- **CMS Integration**: Import content from CMS via API
- **Semantic Search**: Find relevant content using vector embeddings
- **Bubble Chat UI**: Modern, responsive chat interface
- **Real-time Processing**: Upload and query documents in real-time
- **Source Attribution**: See which documents provided the answers

## Tech Stack

### Frontend
- HTML5, CSS3, JavaScript (Vanilla)
- Responsive design with Flexbox/Grid
- Font Awesome icons

### Backend
- Python 3.9+
- FastAPI (REST API framework)
- Uvicorn (ASGI server)

### AI/ML Components
- Sentence Transformers (`all-MiniLM-L6-v2`) for embeddings
- Qdrant Cloud for vector storage and retrieval

### File Processing
- pdfminer.six (PDF parsing)
- python-docx (DOCX parsing)
- pandas (CSV processing)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd project

































# Document Chatbot with CMS Integration

A web-based chatbot that can answer questions based on uploaded documents (PDF, DOCX, CSV, TXT) and imported CMS content using a vector database (Qdrant).

## Features

- **File Upload**: Upload PDF, DOCX, CSV, and TXT files
- **CMS Integration**: Import content from CMS via API
- **Semantic Search**: Find relevant content using vector embeddings
- **Bubble Chat UI**: Modern, responsive chat interface
- **Real-time Processing**: Upload and query documents in real-time
- **Source Attribution**: See which documents provided the answers

## Tech Stack

### Frontend
- HTML5, CSS3, JavaScript (Vanilla)
- Responsive design with Flexbox/Grid
- Font Awesome icons

### Backend
- Python 3.9+
- FastAPI (REST API framework)
- Uvicorn (ASGI server)

### AI/ML Components
- Sentence Transformers (`all-MiniLM-L6-v2`) for embeddings
- Qdrant Cloud for vector storage and retrieval

### File Processing
- pdfminer.six (PDF parsing)
- python-docx (DOCX parsing)
- pandas (CSV processing)

## Setup Instructions

### 1. Clone or Download the Project
```bash
git clone <your-repo-url>
cd document-chatbot