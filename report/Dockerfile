# Backend de signalement Utiq Tracker — zéro dépendance, image minimale.
FROM node:22-alpine

WORKDIR /app
COPY server.mjs store.mjs ./

# node user = uid 1000 (aligné avec ./reports côté hôte). Pas de root au runtime.
USER node
EXPOSE 8090

# Pas de npm install : aucune dépendance externe.
CMD ["node", "server.mjs"]
