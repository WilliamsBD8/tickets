# syntax=docker/dockerfile:1
# Build estático (Vite) y sirve con Nginx; el navegador llama al API bajo /api (mismo origen).
FROM node:22-bookworm-slim AS builder

WORKDIR /app

ENV npm_config_update_notifier=false \
    CI=true

COPY package.json ./
RUN npm install

COPY index.html vite.config.ts tsconfig.json tsconfig.node.json ./
COPY src ./src

RUN npm run build

FROM nginx:1.26-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
