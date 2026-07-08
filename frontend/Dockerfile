FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --include=dev
COPY . .
# VITE_* переменные встраиваются в бандл на этапе сборки. Ключ карты передаётся
# как build-arg из docker-compose (значение берётся из корневого .env).
ARG VITE_YANDEX_API_KEY=""
ENV VITE_YANDEX_API_KEY=$VITE_YANDEX_API_KEY
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / { try_files $uri $uri/ /index.html; }\n}\n' \
    > /etc/nginx/conf.d/default.conf
EXPOSE 80
