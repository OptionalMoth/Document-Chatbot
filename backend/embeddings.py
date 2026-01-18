from sentence_transformers import SentenceTransformer
from typing import List, cast
import numpy as np
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the model
model = None

def get_model():
    """Lazy load the model to save memory"""
    global model
    if model is None:
        logger.info("Loading sentence transformer model...")
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    return model

def embed_text(text: str) -> List[float]:
    """Generate embeddings for text"""
    try:
        # 1. Validation
        if not text or not text.strip():
            raise ValueError("Text cannot be empty for embedding.")
        
        # 2. Text Truncation
        max_length = 10000
        if len(text) > max_length:
            logger.warning(f"Text too long ({len(text)} chars), truncating.")
            text = text[:max_length]
        
        # 3. Model Inference
        # Note: model.encode can return a List[Tensor], np.ndarray, or Tensor.
        # convert_to_numpy=True ensures we get a NumPy array for easier conversion.
        model = get_model()
        embedding = model.encode(
            text, 
            normalize_embeddings=True, 
            convert_to_numpy=True
        )
        
        # 4. Dimension Handling
        # If result is a batch of 1 (e.g., shape [1, 384]), flatten it to [384]
        if isinstance(embedding, np.ndarray):
            if embedding.ndim > 1:
                embedding = embedding.flatten()
            
            # 5. Conversion to List
            # cast() tells VS Code to treat the result as a list of floats
            return cast(List[float], embedding.tolist())
        
        # Fallback if somehow it's not a numpy array
        return [float(x) for x in embedding]
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise ValueError(f"Failed to generate embedding for the provided text: {str(e)}")

def embed_batch(texts: list):
    """Generate embeddings for multiple texts at once"""
    try:
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            return []
        
        model = get_model()
        embeddings = model.encode(valid_texts, normalize_embeddings=True)
        return [embedding.tolist() for embedding in embeddings]
        
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise

def cleanup_model():
    """Clean up model from memory"""
    global model
    import torch
    if model is not None:
        # Clear model from GPU if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        model = None
        logger.info("Model cleaned up from memory")