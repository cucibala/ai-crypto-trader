from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# 创建数据库目录
if not os.path.exists('data'):
    os.makedirs('data')

# 创建数据库引擎
engine = create_engine('sqlite:///data/crypto_trading.db', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Kline(Base):
    """K线数据表"""
    __tablename__ = 'klines'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, 4h, 1d
    open_time = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    close_time = Column(DateTime, nullable=False)
    quote_volume = Column(Float, nullable=False)
    trades_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Kline(symbol='{self.symbol}', interval='{self.interval}', open_time='{self.open_time}')>"

class Trade(Base):
    """交易记录表"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(50), nullable=False, unique=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # LIMIT, MARKET
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)  # NEW, FILLED, CANCELED
    executed_qty = Column(Float, default=0)
    executed_price = Column(Float, default=0)
    fee = Column(Float, default=0)
    fee_asset = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Trade(symbol='{self.symbol}', side='{self.side}', quantity={self.quantity}, price={self.price})>"

class MarketData(Base):
    """市场数据表"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=False)
    price_change_24h = Column(Float, nullable=False)
    price_change_percent_24h = Column(Float, nullable=False)
    high_24h = Column(Float, nullable=False)
    low_24h = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MarketData(symbol='{self.symbol}', price={self.price}, created_at='{self.created_at}')>"

# 创建数据库表
Base.metadata.create_all(engine) 