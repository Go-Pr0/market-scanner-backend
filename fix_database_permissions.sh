#!/bin/bash
# Fix database permissions for Raspberry Pi deployment

echo "🔧 Fixing database permissions..."

# Get the current user
CURRENT_USER=$(whoami)
echo "Current user: $CURRENT_USER"

# Set correct permissions for data directory
echo "Setting permissions for data directory..."
chmod 755 ./data
chmod 644 ./data/*.db 2>/dev/null || echo "No .db files in data directory yet"

# Set correct permissions for bybit database directory
echo "Setting permissions for bybit database directory..."
mkdir -p ./bybit_data_fetcher/database
chmod 755 ./bybit_data_fetcher/database
chmod 644 ./bybit_data_fetcher/database/*.db 2>/dev/null || echo "No .db files in bybit database directory yet"

# Set ownership to current user
echo "Setting ownership to $CURRENT_USER..."
chown -R $CURRENT_USER:$CURRENT_USER ./data 2>/dev/null || echo "Could not change ownership of data directory"
chown -R $CURRENT_USER:$CURRENT_USER ./bybit_data_fetcher 2>/dev/null || echo "Could not change ownership of bybit_data_fetcher directory"

# Create directories if they don't exist
echo "Creating necessary directories..."
mkdir -p ./data
mkdir -p ./bybit_data_fetcher/database
mkdir -p ./logs

# Set permissions for logs
chmod 755 ./logs
chown -R $CURRENT_USER:$CURRENT_USER ./logs 2>/dev/null || echo "Could not change ownership of logs directory"

echo "✅ Database permissions fixed!"
echo ""
echo "📋 Directory structure:"
ls -la ./data 2>/dev/null || echo "data directory not found"
ls -la ./bybit_data_fetcher/database 2>/dev/null || echo "bybit database directory not found"
echo ""
echo "🚀 You can now start the application with:"
echo "uvicorn main:app --host 0.0.0.0 --port 8000"