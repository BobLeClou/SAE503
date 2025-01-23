# Utiliser une image de base officielle
FROM ubuntu:latest

# Mettre à jour les paquets et installer des dépendances de base
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    git \
    && apt-get clean

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de l'application dans le conteneur
COPY . /app

# Exposer le port sur lequel l'application va tourner
EXPOSE 8080

# Commande par défaut pour exécuter l'application
CMD ["bash"]