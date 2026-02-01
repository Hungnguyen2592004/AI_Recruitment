#!/bin/bash
set -e

# Run database migration
python migrate_db.py

# Start the server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
