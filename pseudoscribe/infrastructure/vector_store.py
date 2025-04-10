import numpy as np
from typing import Dict, List, Optional, Any
import logging
from scipy.spatial.distance import cosine

logger = logging.getLogger(__name__)

class VectorStore:
    """Store and retrieve vectors with similarity search capabilities.
    
    This class handles the storage and retrieval of vector embeddings,
    providing similarity search functionality for AI-005.
    """
    
    def __init__(self):
        """Initialize an empty vector store."""
        self.vectors: Dict[str, np.ndarray] = {}
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize the vector store.
        
        Returns:
            bool: True if initialization succeeded
        """
        self.initialized = True
        return True
        
    def add_vector(self, id: str, vector: np.ndarray) -> bool:
        """Add a vector to the store.
        
        Args:
            id: Unique identifier for the vector
            vector: The vector to store
            
        Returns:
            bool: True if vector was added successfully
        """
        if not self.initialized:
            logger.error("Vector store not initialized")
            return False
            
        if not isinstance(vector, np.ndarray):
            logger.error(f"Expected numpy array, got {type(vector)}")
            return False
            
        self.vectors[id] = vector
        return True
        
    def get_vector(self, id: str) -> Optional[np.ndarray]:
        """Retrieve a vector by ID.
        
        Args:
            id: Unique identifier for the vector
            
        Returns:
            np.ndarray or None: The vector if found
        """
        if not self.initialized:
            logger.error("Vector store not initialized")
            return None
            
        return self.vectors.get(id)
        
    def find_similar(self, query_vector: np.ndarray, top_k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Find vectors similar to the query vector.
        
        Args:
            query_vector: The vector to compare against
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of dictionaries with 'id' and 'score' keys
        """
        if not self.initialized:
            logger.error("Vector store not initialized")
            return []
            
        if len(self.vectors) == 0:
            return []
            
        # Validate parameters
        if threshold < 0.0 or threshold > 1.0:
            logger.warning(f"Threshold should be between 0.0 and 1.0, got {threshold}")
            threshold = max(0.0, min(threshold, 1.0))  # Clamp to valid range
            
        # Calculate similarity scores
        similarities = []
        for id, vector in self.vectors.items():
            # Calculate cosine similarity (1 - cosine distance)
            similarity = 1.0 - cosine(query_vector, vector)
            if similarity >= threshold:
                similarities.append((id, similarity))
                
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return [{"id": id, "score": float(score)} for id, score in similarities[:top_k]]
