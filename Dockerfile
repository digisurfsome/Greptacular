# Stage 1: Build React UI
FROM node:20-slim AS ui-builder
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Copy built UI from stage 1
COPY --from=ui-builder /app/ui/dist ./ui/dist

# Railway sets PORT dynamically
ENV PORT=8080
EXPOSE 8080

CMD python -m uvicorn server.main:app --host 0.0.0.0 --port ${PORT}
