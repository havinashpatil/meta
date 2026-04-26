# Multi-stage build: Frontend + Backend + TGI for LLM serving
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# TGI stage for LLM serving
FROM ghcr.io/huggingface/text-generation-inference:3.0.2 AS tgi-builder

# Main stage: Python app with TGI
FROM python:3.10-slim

# Install TGI runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy TGI binary from builder
COPY --from=tgi-builder /usr/local/bin/text-generation-inference /usr/local/bin/

WORKDIR /app

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create cache directories with proper permissions for TGI
RUN mkdir -p /data && chmod 777 /data
RUN mkdir -p /.cache && chmod 777 /.cache
RUN mkdir -p /.triton && chmod 777 /.triton

# Required for HF Spaces: Expose default port 7860 for FastAPI
EXPOSE 7860

# Start both FastAPI server and TGI in background
CMD ["sh", "-c", "text-generation-inference --model-id TinyLlama/TinyLlama-1.1B-Chat-v1.0 --port 8080 --hostname 0.0.0.0 & uvicorn server.app:app --host 0.0.0.0 --port 7860"]
