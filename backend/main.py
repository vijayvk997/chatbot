import requests
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

app = FastAPI()

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hugging Face API Key (Get it from https://huggingface.co/settings/tokens)
HUGGINGFACE_API_KEY = "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"

# Database Configuration
DATABASE_URL = "mysql+pymysql://root:Admin@localhost:3306/chatbot_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    contact_info = Column(Text)
    product_categories = Column(Text)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    brand = Column(String(255))
    price = Column(DECIMAL(10, 2))
    category = Column(String(255))
    description = Column(Text)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define request model
class TextRequest(BaseModel):
    text: str

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Chatbot API is running"}

# Get products by brand
@app.get("/products/{brand}")
def get_products(brand: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.brand == brand).all()
    return {"products": [{"name": p.name, "price": p.price, "category": p.category, "description": p.description} for p in products]}

# Get suppliers by product category
@app.get("/suppliers/{category}")
def get_suppliers(category: str, db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).filter(Supplier.product_categories.contains(category)).all()
    return {"suppliers": [{"name": s.name, "contact": s.contact_info, "categories": s.product_categories} for s in suppliers]}

# Summarization function
def summarize_text_with_huggingface(text: str):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": text}

    response = requests.post(
        "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
        headers=headers,
        json=payload,
    )

    if response.status_code == 200:
        return response.json()[0]["summary_text"]
    else:
        return "Failed to summarize text. Try again later."

# Summarize product description
@app.post("/summarize/product")
def summarize_product(request: TextRequest):
    return {"summary": summarize_text_with_huggingface(request.text)}

# Summarize supplier contact information
@app.post("/summarize/supplier")
def summarize_supplier(request: TextRequest):
    return {"summary": summarize_text_with_huggingface(request.text)}
