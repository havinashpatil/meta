# Multi-stage build: Build frontend with Node.js
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Main stage: Python app
FROM python:3.10-slim

WORKDIR /app

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Required for HF Spaces: Expose default port 7860
EXPOSE 7860

# FastAPI server — points to the new production entrypoint
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
