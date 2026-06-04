# Basis-Image
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Anforderungen installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren (Datenbank zuerst für besseres Caching)
COPY movies.db .
COPY app.py db.py .
COPY static/ ./static/
COPY templates/ ./templates/

# Port freigeben
EXPOSE 8080

# Flask-Konfiguration
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080

# Container-Startbefehl
CMD ["flask", "run"]