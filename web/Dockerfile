FROM node:24-slim

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci && chown -R node:node /app/node_modules

COPY . .
# Docker creates this parent as root when mounting the Transcrypt volume.
CMD ["sh", "-c", "mkdir -p /app/src/generated && chown node:node /app/src/generated && exec su node -c 'npm ci && exec npm run dev'"]
