from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
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
    symbol = Column(String(20), nullable=False)
    interval = Column(String(10), nullable=False)  # 1h, 4h, 1d
    open_time = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    close_time = Column(DateTime, nullable=False)
    quote_volume = Column(Float, nullable=False)
    trades_count = Column(Integer, nullable=False)
    taker_buy_volume = Column(Float, nullable=False)
    taker_buy_quote_volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Kline(symbol='{self.symbol}', interval='{self.interval}', open_time='{self.open_time}')>"

class MarketAnalysis(Base):
    """市场分析数据表"""
    __tablename__ = 'market_analysis'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    price_change_24h = Column(Float)
    volume_24h = Column(Float)
    quote_volume = Column(Float)
    volume_change_24h = Column(Float)
    volume_vs_7d_avg = Column(Float)
    
    # 技术指标数据（使用JSON类型存储）
    rsi_data = Column(JSON)  # {'1d': value, '4h': value, '1h': value}
    macd_data = Column(JSON)  # {'1d': {macd, signal, histogram}, '4h': {...}, '1h': {...}}
    bollinger_data = Column(JSON)  # {'1d': value, '4h': value, '1h': value}
    price_trends = Column(JSON)  # 存储价格趋势分析结果
    
    # AI分析结果
    analysis_result = Column(JSON)  # 存储GPT模型的分析结果
    strategy = Column(JSON)  # 存储生成的交易策略
    
    # 请求相关信息
    request_ip = Column(String(50))
    request_timestamp = Column(DateTime)
    response_time = Column(Float)  # 响应时间（毫秒）
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketAnalysis(symbol='{self.symbol}', timestamp='{self.timestamp}')>"

# 创建数据库表
Base.metadata.create_all(engine) 