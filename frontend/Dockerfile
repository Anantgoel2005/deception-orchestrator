FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV API_HOST=backend
RUN npm run build
RUN chown -R node:node /app

EXPOSE 3000

USER node
CMD ["npm", "start"]
