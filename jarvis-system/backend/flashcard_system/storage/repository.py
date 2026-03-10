"""Repository pattern implementation for data access."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class Repository:
    """
    Base repository class providing unified data access interface.
    Implements the repository pattern for database operations.
    """
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def create(self, entity: Any) -> Any:
        """
        Create and persist a new entity.
        
        Args:
            entity: Entity instance to create
        
        Returns:
            Created entity
        """
        try:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            logger.info(f"Created entity: {entity.__class__.__name__}")
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating entity: {str(e)}")
            raise
    
    def read(self, entity_class: Any, entity_id: int) -> Optional[Any]:
        """
        Read entity by ID.
        
        Args:
            entity_class: Entity class to read
            entity_id: ID of entity to read
        
        Returns:
            Entity instance or None
        """
        try:
            return self.session.query(entity_class).filter(
                entity_class.id == entity_id
            ).first()
        except Exception as e:
            logger.error(f"Error reading entity: {str(e)}")
            return None
    
    def read_all(self, entity_class: Any, skip: int = 0, limit: int = 100) -> List[Any]:
        """
        Read all entities with pagination.
        
        Args:
            entity_class: Entity class to read
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of entity instances
        """
        try:
            return self.session.query(entity_class).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error reading all entities: {str(e)}")
            return []
    
    def update(self, entity: Any) -> Any:
        """
        Update an existing entity.
        
        Args:
            entity: Entity instance to update
        
        Returns:
            Updated entity
        """
        try:
            self.session.merge(entity)
            self.session.commit()
            logger.info(f"Updated entity: {entity.__class__.__name__}")
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating entity: {str(e)}")
            raise
    
    def delete(self, entity: Any) -> bool:
        """
        Delete an entity.
        
        Args:
            entity: Entity instance to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.session.delete(entity)
            self.session.commit()
            logger.info(f"Deleted entity: {entity.__class__.__name__}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting entity: {str(e)}")
            return False
    
    def execute_query(self, query: Any) -> List[Any]:
        """
        Execute a raw query.
        
        Args:
            query: SQLAlchemy query object
        
        Returns:
            Query results
        """
        try:
            return query.all()
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return []
