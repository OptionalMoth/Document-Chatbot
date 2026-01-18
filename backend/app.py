from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from transformers import pipeline # Add this
from document_parser import parse_file
from embeddings import embed_text
from qdrant_utils import store_vectors, search_vectors
from pydantic import BaseModel
import logging
import json
import tempfile
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Chatbot API")

# Initialize the generation pipeline 
generator = pipeline("text2text-generation", model="google/flan-t5-large")

# Models for request bodies
class ChatRequest(BaseModel):
    query: str

class CMSContent(BaseModel):
    content: str
    source: str = "cms"
    metadata: dict = {}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Document Chatbot API is running"}


import os
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# ... other imports ...

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process document files (PDF, DOCX, CSV, TXT)"""
    try:
        # 1. Safely handle the filename for splitext
        # We use a fallback empty string to satisfy the type checker
        raw_filename = file.filename or "unknown_file"
        logger.info(f"Processing upload: {raw_filename}")
        
        # 2. Extract extension safely
        _, file_ext = os.path.splitext(raw_filename)
        file_ext = file_ext.lower()
        
        allowed_extensions = ['.pdf', '.docx', '.csv', '.txt']
        if not file_ext or file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type '{file_ext}' not supported. Use: {', '.join(allowed_extensions)}"
            )
        
        # 3. Use a context manager for the temporary file
        # 'delete=False' is important because some parsers need the file to be closed 
        # before they can open it themselves.
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # 4. Parse file
            # Passing raw_filename ensures our metadata is accurate even if tmp_path is cryptic
            chunks = parse_file(tmp_path, raw_filename)
            logger.info(f"Parsed {len(chunks)} chunks from {raw_filename}")
            
            if not chunks:
                raise HTTPException(status_code=400, detail="No content extracted.")
            
            # 5. Generate embeddings & Prepare Data
            vectors = []
            payloads = []
            
            for i, chunk in enumerate(chunks):
                if chunk and chunk.strip():
                    try:
                        vector = embed_text(chunk)
                        vectors.append(vector)
                        payloads.append({
                            "text": chunk,
                            "source": raw_filename,
                            "type": "file",
                            "file_type": file_ext,
                            "chunk_id": i
                        })
                    except Exception as e:
                        logger.warning(f"Skipping chunk {i+1}: {e}")
            
            if not vectors:
                raise HTTPException(status_code=400, detail="Failed to generate embeddings.")
            
            # 6. Store in Qdrant
            success = store_vectors(vectors, payloads)
            
            if not success:
                raise HTTPException(status_code=500, detail="Database storage failed.")
            
            return JSONResponse({
                "status": "success",
                "filename": raw_filename,
                "chunks_processed": len(payloads)
            })
                
        finally:
            # 7. Cleanup is guaranteed even if parsing fails
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during processing.")

@app.post("/import-cms")
async def import_cms(cms_content: CMSContent):
    """Import content from CMS (simulated with JSON)"""
    try:
        logger.info(f"Importing CMS content from: {cms_content.source}")
        
        # Split content into chunks with better sentence detection
        import re
        
        # Better sentence splitting that handles abbreviations, decimals, etc.
        sentence_endings = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s+(?=[A-Z])'
        chunks = re.split(sentence_endings, cms_content.content)
        
        # Clean and filter chunks
        cleaned_chunks = []
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk and len(chunk) > 10:  # Minimum length to avoid tiny fragments
                cleaned_chunks.append(chunk)
        
        chunks = cleaned_chunks
        logger.info(f"Split into {len(chunks)} text chunks")
        
        # Generate embeddings
        vectors = []
        valid_chunks = []
        
        for chunk in chunks:
            try:
                vector = embed_text(chunk)
                vectors.append(vector)
                valid_chunks.append(chunk)
            except Exception as e:
                logger.warning(f"Skipping chunk: {e}")
        
        if not vectors:
            raise HTTPException(
                status_code=400, 
                detail="Failed to generate embeddings from CMS content"
            )
        
        # Prepare payloads
        payloads = []
        for chunk in valid_chunks:
            payloads.append({
                "text": chunk,
                "source": cms_content.source,
                "type": "cms",
                "metadata": cms_content.metadata
            })
        
        # Store in Qdrant
        success = store_vectors(vectors, payloads)
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Failed to store CMS content in database"
            )
        
        return JSONResponse({
            "status": "success",
            "source": cms_content.source,
            "chunks": len(valid_chunks),
            "message": "CMS content imported successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CMS import error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    """Process chat queries and return AI-generated answers based on stored content"""
    try:
        logger.info(f"Chat query: {request.query}")
        
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # 1. Generate embedding for query
        query_vector = embed_text(request.query)
        
        # 2. Search for similar content with more results for better context
        hits = search_vectors(query_vector, limit=5, score_threshold=0.3)
        
        if not hits:
            return {
                "answer": "I couldn't find any relevant information in the documents. Please try a different question or upload more relevant documents.",
                "sources": []
            }
        
        # 3. Construct better context by filtering and organizing chunks
        # Sort by score and remove very low-quality matches
        sorted_hits = sorted(hits, key=lambda x: x["score"], reverse=True)
        filtered_hits = [hit for hit in sorted_hits if hit["score"] > 0.4]
        
        if not filtered_hits:
            filtered_hits = sorted_hits[:2]  # Use top 2 even if scores are low
        
        # Create organized context with better formatting
        context_parts = []
        for i, hit in enumerate(filtered_hits[:3], 1):  # Use top 3 max
            text = hit["payload"]["text"]
            # Clean up the text - remove leading/trailing punctuation
            text = re.sub(r'^[^a-zA-Z0-9"\']+', '', text)
            text = re.sub(r'[^a-zA-Z0-9"\'.!?]+$', '', text)
            
            context_parts.append(f"[Excerpt {i}]: {text}")
        
        context_text = "\n\n".join(context_parts)
        
        # 4. Create a more specific prompt with clear instructions
        prompt = f"""Based on the following document excerpts, answer the user's question.
If the answer cannot be found in the excerpts, say "I don't have enough information to answer that question based on the provided documents."

DOCUMENT EXCERPTS:
{context_text}

QUESTION: {request.query}

INSTRUCTIONS:
- Answer in a clear, complete sentence
- Do not use bullet points or numbered lists
- Reference the excerpts if they contain the answer
- If excerpts conflict, mention any uncertainties

ANSWER:"""
        
        # 5. Generate answer with improved parameters
        result = generator(
            prompt, 
            max_new_tokens=200, 
            do_sample=True,  # Allow sampling for more natural responses
            temperature=0.3,  # Lower temperature for more focused answers
            repetition_penalty=1.2  # Avoid repetition
        )
        generated_answer = result[0]['generated_text'].strip()
        
        # 6. Post-process the answer to remove common artifacts
        # Remove incomplete sentence starters
        invalid_starts = ["i. ", "ii. ", "iii. ", "iv. ", "v. ", "- ", "* "]
        for invalid in invalid_starts:
            if generated_answer.lower().startswith(invalid):
                generated_answer = generated_answer[len(invalid):].capitalize()
        
        # Ensure it ends with proper punctuation
        if generated_answer and generated_answer[-1] not in ['.', '!', '?']:
            generated_answer += '.'
        
        # 7. Prepare sources
        sources = []
        for hit in filtered_hits[:3]:
            source_text = hit["payload"]["text"]
            # Truncate intelligently at sentence boundary
            if len(source_text) > 250:
                # Try to cut at sentence end
                last_period = source_text[:250].rfind('. ')
                if last_period > 100:
                    source_text = source_text[:last_period + 1] + "..."
                else:
                    source_text = source_text[:247] + "..."
            
            sources.append({
                "text": source_text,
                "score": round(hit["score"], 3),
                "source": hit["payload"].get("source", "Unknown"),
                "type": hit["payload"].get("type", "unknown")
            })
        
        return {
            "answer": generated_answer,
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "document-chatbot"}

@app.delete("/clear")
async def clear_database():
    """Clear all vectors from the database (for testing/reset)"""
    try:
        from qdrant_utils import client, COLLECTION_NAME
        client.delete_collection(collection_name=COLLECTION_NAME)
        return {"status": "success", "message": "Database cleared"}
    except Exception as e:
        logger.error(f"Clear database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))