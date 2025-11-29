from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# check_same_thread=False is needed only for SQLite
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class PinnedChart(Base):
    __tablename__ = "pinned_charts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    title = Column(String)
    chart_type = Column(String)
    chart_config = Column(Text) # Stores the Plotly JSON as a string
    timestamp = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()