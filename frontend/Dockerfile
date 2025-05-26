FROM nginx:mainline-alpine3.18-slim

COPY ./dist /html/web

COPY ./deploy/startup.sh /docker-entrypoint.d/

# Make startup script executable
RUN chmod +x /docker-entrypoint.d/startup.sh

EXPOSE 3000