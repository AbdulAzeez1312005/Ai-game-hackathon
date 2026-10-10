FROM node:22-alpine AS frontend-build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY frontend ./frontend
COPY vite.config.js postcss.config.js tailwind.config.js ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    SESSION_COOKIE_SECURE=true

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ai_logic.py game_logic.py ./
COPY templates ./templates
COPY models ./models
COPY --from=frontend-build /app/static/dist ./static/dist

EXPOSE 10000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 app:app"]
