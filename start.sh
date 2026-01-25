#!/bin/bash
# Railway deployment script for Streamlit
export PORT=${PORT:-8501}
echo "Starting Streamlit on port $PORT"
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true