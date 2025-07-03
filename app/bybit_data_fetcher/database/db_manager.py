"""
Database manager for storing and retrieving market data.
"""
import os
import aiosqlite
import pandas as pd
from datetime import datetime
import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_manager')

class DatabaseManager:
    def __init__(self, db_path):
        """Initialize database manager."""
        self.db_path = db_path
        self.conn = None
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def connect(self):
        """Connect to the database."""
        if self.conn is None:
            self.conn = await aiosqlite.connect(self.db_path)
            await self._create_tables()

    async def close(self):
        """Close the database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def _create_tables(self):
        """Create necessary tables if they don't exist."""
        async with self.conn.cursor() as cursor:
            # Create table for candle data
            await cursor.execute('''
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
                UNIQUE(symbol, timestamp)
            )
            ''')
            
            # Create index for faster queries
            await cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON candle_data (symbol, timestamp)
            ''')
        
        await self.conn.commit()

    async def get_latest_candle_timestamp(self, symbol):
        """Get the timestamp of the latest candle for a given symbol."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT MAX(timestamp) FROM candle_data WHERE symbol = ?
            ''', (symbol,))
            
            result = await cursor.fetchone()
            return result[0] if result and result[0] else None

    async def get_candle_count(self, symbol):
        """Get the total number of candles for a given symbol."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT COUNT(*) FROM candle_data WHERE symbol = ?
            ''', (symbol,))
            
            result = await cursor.fetchone()
            return result[0] if result and result[0] else 0

    async def get_earliest_candle_timestamp(self, symbol):
        """Get the timestamp of the earliest candle for a given symbol."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT MIN(timestamp) FROM candle_data WHERE symbol = ?
            ''', (symbol,))
            
            result = await cursor.fetchone()
            return result[0] if result and result[0] else None

    async def save_candles(self, symbol, candles_df):
        """Save candle data to the database."""
        if candles_df.empty:
            logger.warning(f"No candles to save for {symbol}")
            return 0
        
        # Make a copy to avoid modifying the original DataFrame
        df = candles_df.copy()
        
        # Convert timestamp to milliseconds if it's in datetime format
        if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = df['timestamp'].astype(int) // 10**6
        
        try:
            # Add symbol to the DataFrame
            df['symbol'] = symbol

            # Prepare data for insertion
            cols = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            to_insert = [tuple(x) for x in df[cols].to_numpy()]

            # Use executemany for batch insert
            async with self.conn.cursor() as cursor:
                await cursor.executemany('''
                INSERT OR IGNORE INTO candle_data 
                (symbol, timestamp, open, high, low, close, volume, turnover)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', to_insert)
                
                await self.conn.commit()
                count = cursor.rowcount
                
            logger.info(f"Saved {count} new candles for {symbol}")
            return count
        except Exception as e:
            logger.error(f"Error saving candles for {symbol}: {str(e)}")
            try:
                await self.conn.rollback()
            except:
                pass
            return 0

    async def get_candle_range(self, symbol, start_timestamp=None, end_timestamp=None, limit=1000):
        """Get a range of candles for a symbol."""
        async with self.conn.cursor() as cursor:
            query = '''
            SELECT timestamp, open, high, low, close, volume, turnover
            FROM candle_data
            WHERE symbol = ?
            '''
            params = [symbol]
            
            if start_timestamp:
                query += ' AND timestamp >= ?'
                params.append(start_timestamp)
            
            if end_timestamp:
                query += ' AND timestamp <= ?'
                params.append(end_timestamp)
            
            query += ' ORDER BY timestamp ASC LIMIT ?'
            params.append(limit)
            
            await cursor.execute(query, tuple(params))
            
            rows = await cursor.fetchall()
            if not rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
    
    async def get_latest_candles(self, symbol, limit=1000):
        """Get the latest N candles for a symbol (most recent first)."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT timestamp, open, high, low, close, volume, turnover
            FROM candle_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
            ''', (symbol, limit))
            
            rows = await cursor.fetchall()
            if not rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Sort by timestamp ascending (oldest first) for EMA calculations
            df = df.sort_values('timestamp')
            return df
