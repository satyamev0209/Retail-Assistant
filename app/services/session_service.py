"""Session service for managing temporary uploads."""
from typing import Dict, Set
from pathlib import Path
from app.core.config import settings
from app.services.sql_service import sql_service
import logging
import shutil

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing temporary session data."""
    
    def __init__(self):
        """Initialize session service."""
        self.sessions: Dict[str, Set[str]] = {}  # session_id -> set of temp table names
        self.session_files: Dict[str, Set[str]] = {}  # session_id -> set of file paths
    
    def register_temp_table(self, session_id: str, table_name: str) -> None:
        """
        Register a temporary table for a session.
        
        Args:
            session_id: Session identifier
            table_name: Name of temporary table
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = set()
        self.sessions[session_id].add(table_name)
        logger.info(f"Registered temp table '{table_name}' for session {session_id}")
    
    def register_temp_file(self, session_id: str, file_path: str) -> None:
        """
        Register a temporary file for a session.
        
        Args:
            session_id: Session identifier
            file_path: Path to temporary file
        """
        if session_id not in self.session_files:
            self.session_files[session_id] = set()
        self.session_files[session_id].add(file_path)
        logger.info(f"Registered temp file '{file_path}' for session {session_id}")
    
    def cleanup_session(self, session_id: str) -> None:
        """
        Clean up all temporary data for a session.
        
        Args:
            session_id: Session identifier
        """
        try:
            # Clean up temp tables
            if session_id in self.sessions:
                for table_name in self.sessions[session_id]:
                    try:
                        sql_service.drop_table(table_name)
                    except Exception as e:
                        logger.warning(f"Error dropping table {table_name}: {e}")
                
                del self.sessions[session_id]
                logger.info(f"Cleaned up temp tables for session {session_id}")
            
            # Clean up temp files
            if session_id in self.session_files:
                for file_path in self.session_files[session_id]:
                    try:
                        Path(file_path).unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"Error deleting file {file_path}: {e}")
                
                del self.session_files[session_id]
                logger.info(f"Cleaned up temp files for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up session: {e}")
    
    def get_session_tables(self, session_id: str) -> Set[str]:
        """Get all temporary tables for a session."""
        return self.sessions.get(session_id, set())
    
    def get_session_files(self, session_id: str) -> Set[str]:
        """Get all temporary files for a session."""
        return self.session_files.get(session_id, set())


# Global session service instance
session_service = SessionService()
