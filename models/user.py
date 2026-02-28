from sqlalchemy import Column, String, DateTime, Integer,ForeignKey
from sqlalchemy.sql import func
from core.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())
    
    refresh_tokens = relationship("RefreshToken",back_populates="user")
    conversations = relationship("Conversation",back_populates="user")
    memories = relationship("UserMemory",back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True),nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())

    user = relationship("User",back_populates="refresh_tokens")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())

    user = relationship("User",back_populates="conversations")


class UserMemory(Base):
    __tablename__ = "user_memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fact = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())

    user = relationship("User",back_populates="memories")

