FROM alpine:latest

WORKDIR /app

# Installer les dépendances nécessaires
RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    build-base \
    libffi-dev \
    rust \
    cargo

# Créer et activer un environnement virtuel
RUN python3 -m venv venv
ENV PATH="/app/venv/bin:$PATH"

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001

CMD ["python", "app.py"]
