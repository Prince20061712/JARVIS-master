from datetime import datetime
from typing import List, Optional
import json
import pickle

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, LargeBinary, TypeDecorator
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class JSONType(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

class VectorType(TypeDecorator):
    """
    Stores numpy array as bytes (Pickle) because SQLite doesn't support arrays natively.
    For production vector DBs, use pgvector or distinct vector stores.
    """
    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return pickle.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return pickle.loads(value)

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    role = Column(String(20)) # 'user', 'system'
    content = Column(Text)
    embedding = Column(VectorType) # Store embedding blob
    metadata_ = Column("metadata", JSONType, default={})

    def __repr__(self):
        return f"<Conversation(id={self.id}, role={self.role}, timestamp={self.timestamp})>"

class Fact(Base):
    __tablename__ = 'facts'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    topic = Column(String(50))
    content = Column(Text)
    confidence = Column(Float, default=1.0)
    embedding = Column(VectorType)

    def __repr__(self):
        return f"<Fact(id={self.id}, topic={self.topic})>"
