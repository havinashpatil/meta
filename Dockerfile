# Multi-stage build: Frontend + Backend + TGI for LLM serving
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Main stage: Python app with TGI runtime
FROM ghcr.io/huggingface/text-generation-inference:3.0.2

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

# Required for HF Spaces: Expose default ports for FastAPI and TGI
EXPOSE 7860
EXPOSE 8080

# Override the TGI base image entrypoint and start both TGI + FastAPI
ENTRYPOINT ["/bin/sh", "-c", "text-generation-inference --model-id TinyLlama/TinyLlama-1.1B-Chat-v1.0 --port 8080 --hostname 0.0.0.0 & uvicorn server.app:app --host 0.0.0.0 --port 7860"]
