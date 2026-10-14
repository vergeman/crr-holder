FROM node:24-slim

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci && chown -R node:node /app/node_modules

COPY . .
USER node
CMD ["npm", "run", "dev"]
