FROM nginx:mainline-alpine3.18-slim

COPY ./build /html/web

COPY ./deploy/startup.sh /docker-entrypoint.d/

EXPOSE 80