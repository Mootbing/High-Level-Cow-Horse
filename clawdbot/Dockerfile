FROM node:22-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Auth state is persisted via volume
CMD ["node", "index.js"]
