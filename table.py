# Datatypes
from sqlalchemy import Integer, String, Float, Boolean, Date, DateTime, Column, create_engine
# ORM tools
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime as dt

Base = declarative_base()
engine = create_engine("sqlite:///mydb.db")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

class patient(Base):
    __tablename__ = "appointements"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, nullable=False,index=True)
    reason = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False,index=True)
    canceled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.utcnow)

def init_db()-> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#https://github.com/chandann461/Schedule_appointement.git