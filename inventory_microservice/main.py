# main.py

import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base

# --- Database Setup (using SQLite for local dev, but ready for PostgreSQL) ---
# For Render.com, we'll set this environment variable to a PostgreSQL connection string.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./store.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models (How data is stored in the DB) ---

class ProductDB(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    stock = Column(Integer)
    orders = relationship("OrderDB", back_populates="product")

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    total_price = Column(Float)
    status = Column(String, default="pending")
    product = relationship("ProductDB", back_populates="orders")

# Create the database tables
Base.metadata.create_all(bind=engine)

# --- Pydantic Models (How data looks in API requests/responses) ---

class ProductBase(BaseModel):
    name: str
    price: float
    stock: int

class Product(ProductBase):
    id: int
    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    id: int
    product_id: int
    quantity: int
    total_price: float
    status: str
    class Config:
        orm_mode = True

class PaymentWebhook(BaseModel):
    order_id: int
    # In a real app, you'd have more fields like payment_id, secret_key, etc.

# --- Dependency for getting a DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI App Initialization ---
app = FastAPI(title="Orders & Inventory Microservice")

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Orders & Inventory API"}

# --- Product CRUD Endpoints ---

@app.post("/products", response_model=Product, status_code=201)
def create_product(product: ProductBase, db: Session = Depends(get_db)):
    db_product = ProductDB(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product
    
@app.get("/products", response_model=list[Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(ProductDB).offset(skip).limit(limit).all()
    return products

# --- Order Logic ---

@app.post("/orders", response_model=Order, status_code=201)
def create_order(order: OrderBase, db: Session = Depends(get_db)):
    # 1. Find the product
    db_product = db.query(ProductDB).filter(ProductDB.id == order.product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # 2. Check for sufficient stock
    if db_product.stock < order.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
        
    # 3. Reduce stock and create the order in a single transaction
    db_product.stock -= order.quantity
    
    total_price = db_product.price * order.quantity
    db_order = OrderDB(product_id=order.product_id, quantity=order.quantity, total_price=total_price)
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    return db_order

@app.get("/orders/{order_id}", response_model=Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

# --- Payment Webhook Endpoint ---

@app.post("/webhooks/payment")
def payment_webhook(payload: PaymentWebhook, db: Session = Depends(get_db)):
    order_id = payload.order_id
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if db_order.status == "paid":
        return {"message": "Order is already marked as paid"}

    db_order.status = "paid"
    db.commit()
    
    return {"message": f"Order {order_id} has been marked as paid"}
