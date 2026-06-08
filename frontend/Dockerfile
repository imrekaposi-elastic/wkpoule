# Build context MUST be ./frontend. Nginx proxies /api to ${API_HOST}:8000 (K8s/OpenShift: wkpoule-api service).
# See: openshift/README.md, Makefile (build-frontend), docker-compose service `frontend`.

FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# OpenShift/Git builds often omit build-args; empty value becomes "" in the bundle and RUM sends no environment.
ARG VITE_APM_ENVIRONMENT=prd
ENV VITE_APM_ENVIRONMENT=$VITE_APM_ENVIRONMENT
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY runtime-config.js.template /etc/wkpoule/runtime-config.js.template
COPY docker-entrypoint.d/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
# OpenShift arbitrary UID + root group: allow entrypoint to write runtime-config.js and nginx paths.
RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh \
    && chgrp -R 0 /var/cache/nginx /var/run /etc/nginx/conf.d /usr/share/nginx/html \
    && chmod -R g=u /var/cache/nginx /var/run /etc/nginx/conf.d /usr/share/nginx/html
ENV API_HOST=api
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
