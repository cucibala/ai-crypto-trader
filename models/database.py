from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import json

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

class Position(Base):
    """仓位信息表"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # LONG or SHORT
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    status = Column(String(20), nullable=False)  # OPEN, CLOSED
    pnl = Column(Float, default=0.0)
    entry_time = Column(DateTime, default=datetime.utcnow)
    close_time = Column(DateTime)
    close_price = Column(Float)
    conversation_history = Column(Text)  # 存储JSON格式的对话历史

class MarketAnalysis(Base):
    """市场分析记录表"""
    __tablename__ = 'market_analysis'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    market_trend = Column(String(50))
    market_sentiment = Column(String(50))
    confidence = Column(Float)
    analysis_text = Column(Text)

class TradingStrategy(Base):
    """交易策略记录表"""
    __tablename__ = 'trading_strategies'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(50))
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    risk_level = Column(String(20))
    reasoning = Column(Text)

# 创建数据库表
Base.metadata.create_all(engine)

# 创建数据库连接
def init_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'trading.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

# 获取数据库会话
Session = init_db()

def get_current_position():
    """获取当前开放的仓位"""
    session = Session()
    try:
        position = session.query(Position).filter(Position.status == 'OPEN').first()
        return position
    finally:
        session.close()

def create_position(symbol, side, entry_price, quantity, stop_loss, take_profit, conversation_history):
    """创建新仓位"""
    session = Session()
    try:
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status='OPEN',
            conversation_history=json.dumps(conversation_history)
        )
        session.add(position)
        session.commit()
        return position
    finally:
        session.close()

def update_position(position_id, **kwargs):
    """更新仓位信息"""
    session = Session()
    try:
        position = session.query(Position).filter(Position.id == position_id).first()
        if position:
            for key, value in kwargs.items():
                if hasattr(position, key):
                    setattr(position, key, value)
            session.commit()
            return position
        return None
    finally:
        session.close()

def close_position(position_id, close_price, pnl):
    """关闭仓位"""
    session = Session()
    try:
        position = session.query(Position).filter(Position.id == position_id).first()
        if position:
            position.status = 'CLOSED'
            position.close_price = close_price
            position.close_time = datetime.utcnow()
            position.pnl = pnl
            session.commit()
            return position
        return None
    finally:
        session.close()

def get_position_history(limit=10):
    """获取历史仓位记录"""
    session = Session()
    try:
        positions = session.query(Position).order_by(Position.entry_time.desc()).limit(limit).all()
        return positions
    finally:
        session.close()

def save_market_analysis(analysis_text, market_trend=None, market_sentiment=None, confidence=None):
    """保存市场分析"""
    session = Session()
    try:
        analysis = MarketAnalysis(
            analysis_text=analysis_text,
            market_trend=market_trend,
            market_sentiment=market_sentiment,
            confidence=confidence
        )
        session.add(analysis)
        session.commit()
        return analysis
    finally:
        session.close()

def get_recent_market_analysis(limit=5):
    """获取最近的市场分析"""
    session = Session()
    try:
        analyses = session.query(MarketAnalysis).order_by(MarketAnalysis.timestamp.desc()).limit(limit).all()
        return analyses
    finally:
        session.close()

def save_trading_strategy(strategy_text, action=None, entry_price=None, stop_loss=None, take_profit=None, risk_level=None):
    """保存交易策略"""
    session = Session()
    try:
        strategy = TradingStrategy(
            reasoning=strategy_text,
            action=action,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_level=risk_level
        )
        session.add(strategy)
        session.commit()
        return strategy
    finally:
        session.close()

def get_recent_strategies(limit=5):
    """获取最近的交易策略"""
    session = Session()
    try:
        strategies = session.query(TradingStrategy).order_by(TradingStrategy.timestamp.desc()).limit(limit).all()
        return strategies
    finally:
        session.close() 