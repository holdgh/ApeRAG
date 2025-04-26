FROM nginx:mainline-alpine3.18-slim

COPY ./dist /html/web

COPY ./deploy/startup.sh /docker-entrypoint.d/

EXPOSE 3000