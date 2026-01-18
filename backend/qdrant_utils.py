from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct, Distance
from qdrant_client.http import exceptions
import uuid
import logging
import os
import threading
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file in the same directory
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Qdrant configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

if not QDRANT_URL:
    raise ValueError("QDRANT_URL environment variable is not set")

logger.info(f"Connecting to Qdrant at: {QDRANT_URL}")

# Initialize Qdrant client
if QDRANT_API_KEY:
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30
    )
else:
    # For local Qdrant without authentication
    client = QdrantClient(
        url=QDRANT_URL,
        timeout=30
    )

COLLECTION_NAME = "documents"
COLLECTION_LOCK = threading.Lock()

def ensure_collection():
    """Create collection if it doesn't exist"""
    with COLLECTION_LOCK:
        try:
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if COLLECTION_NAME not in collection_names:
                logger.info(f"Creating collection: {COLLECTION_NAME}")
                client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Collection {COLLECTION_NAME} created successfully")
            else:
                logger.debug(f"Collection {COLLECTION_NAME} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise

def store_vectors(vectors: list, payloads: list):
    """Store vectors in Qdrant"""
    if len(vectors) != len(payloads):
        raise ValueError("Vectors and payloads must have the same length")
    
    ensure_collection()
    
    points = []
    for i, (vector, payload) in enumerate(zip(vectors, payloads)):
        # Validate vector dimensions
        if len(vector) != 384:
            logger.warning(f"Vector {i} has wrong dimension: {len(vector)} instead of 384")
            continue
        
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload
        )
        points.append(point)
    
    if not points:
        logger.error("No valid points to store")
        return False
    
    logger.info(f"Storing {len(points)} vectors in Qdrant")
    
    try:
        operation_info = client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        logger.info(f"Successfully stored vectors. Status: {operation_info.status}")
        return True
    except Exception as e:
        logger.error(f"Failed to store vectors: {e}")
        return False

def search_vectors(query_vector, limit=5, score_threshold=0.25):
    """Search for similar vectors in Qdrant"""
    ensure_collection()
    
    try:
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
        
        results = []
        for hit in search_result:
            results.append({
                "payload": hit.payload,
                "score": hit.score
            })
        
        logger.info(f"Search returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

def clear_collection():
    """Clear all vectors from collection"""
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
        logger.info(f"Collection {COLLECTION_NAME} deleted")
        return True
    except Exception as e:
        logger.error(f"Error clearing collection: {e}")
        return False

def get_collection_info():
    try:
        collection_info = client.get_collection(collection_name=COLLECTION_NAME)
        return {
            "name": COLLECTION_NAME,
            "vectors_count": collection_info.points_count,
            "status": str(collection_info.status)
        }
    except exceptions.UnexpectedResponse as e:
        if e.status_code == 404:
            logger.warning(f"Collection {COLLECTION_NAME} does not exist yet.")
            return {"name": COLLECTION_NAME, "status": "not_created", "vectors_count": 0}
        raise e

