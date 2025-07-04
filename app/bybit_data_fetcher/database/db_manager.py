"""
Database manager for storing and retrieving market data.
"""
import os
import aiosqlite
import pandas as pd
from datetime import datetime
import logging
import asyncio
from typing import Optional, List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_manager')

class DatabaseManager:
    def __init__(self, db_path: str):
        """Initialize database manager."""
        self.db_path = db_path
        self.conn = None
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def connect(self):
        """Connect to the database."""
        if self.conn is None:
            self.conn = await aiosqlite.connect(self.db_path)
            await self.create_tables()

    async def close(self):
        """Close the database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def create_tables(self):
        """Create the candle_data table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS candle_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            turnover REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
        """
        
        await self.conn.execute(create_table_sql)
        
        # Create index for faster queries
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
        ON candle_data (symbol, timestamp)
        """
        await self.conn.execute(index_sql)
        await self.conn.commit()
        logger.debug("Tables and indexes created/verified")

    async def save_candles(self, symbol: str, candles_df: pd.DataFrame) -> int:
        """
        Save candles to the database
        
        Args:
            symbol: Trading symbol
            candles_df: DataFrame with candle data
            
        Returns:
            Number of new candles saved
        """
        if candles_df.empty:
            return 0
            
        # Ensure timestamp column is int milliseconds
        ts_col = candles_df['timestamp']
        if pd.api.types.is_datetime64_any_dtype(ts_col):
            candles_df = candles_df.copy()
            candles_df['timestamp'] = (candles_df['timestamp'].astype('int64') // 10**6)
        else:
            # if it's already numeric but in seconds, detect heuristic (<1e12) then multiply by 1000
            if ts_col.dtype.kind in {'i','u','f'} and ts_col.max() < 1e12:
                candles_df = candles_df.copy()
                candles_df['timestamp'] = candles_df['timestamp'] * 1000

        # Convert DataFrame to list of tuples for insertion
        candles_data = [
            (
                symbol,
                int(row['timestamp']),
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume']),
                float(row['turnover'])
            )
            for _, row in candles_df.iterrows()
        ]
        
        # Insert candles with IGNORE to handle duplicates
        insert_sql = """
        INSERT OR IGNORE INTO candle_data 
        (symbol, timestamp, open, high, low, close, volume, turnover)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = await self.conn.executemany(insert_sql, candles_data)
        await self.conn.commit()
        
        new_candles = cursor.rowcount
        logger.debug(f"Saved {new_candles} new candles for {symbol}")
        return new_candles
    
    async def get_latest_candle_timestamp(self, symbol: str) -> Optional[int]:
        """Get the timestamp of the latest candle for a symbol"""
        query = """
        SELECT MAX(timestamp) FROM candle_data 
        WHERE symbol = ?
        """
        
        cursor = await self.conn.execute(query, (symbol,))
        result = await cursor.fetchone()
        
        if result and result[0]:
            return int(result[0])
        return None
    
    async def get_latest_candles(self, symbol: str, limit: int = 1000) -> pd.DataFrame:
        """Get the latest candles for a symbol"""
        query = """
        SELECT timestamp, open, high, low, close, volume, turnover
        FROM candle_data 
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        
        cursor = await self.conn.execute(query, (symbol, limit))
        rows = await cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Sort by timestamp ascending (oldest first)
        df = df.sort_values('timestamp')
        
        return df
    
    async def get_candle_range(self, symbol: str, start_timestamp: int, end_timestamp: int, limit: int = 1000) -> pd.DataFrame:
        """Get candles within a timestamp range"""
        query = """
        SELECT timestamp, open, high, low, close, volume, turnover
        FROM candle_data 
        WHERE symbol = ? AND timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC
        LIMIT ?
        """
        
        cursor = await self.conn.execute(query, (symbol, start_timestamp, end_timestamp, limit))
        rows = await cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
