# Build context MUST be ./frontend. Nginx proxies /api to ${API_HOST}:8000 (K8s/OpenShift: wkpoule-api service).
# See: openshift/README.md, Makefile (build-frontend), docker-compose service `frontend`.

FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# Optional RUM secretToken for Elastic APM (same value as Fleet / APM integration RUM secret).
ARG VITE_ELASTIC_APM_RUM_SECRET
ENV VITE_ELASTIC_APM_RUM_SECRET=$VITE_ELASTIC_APM_RUM_SECRET
ARG VITE_APM_ENVIRONMENT
ENV VITE_APM_ENVIRONMENT=$VITE_APM_ENVIRONMENT
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template
# OpenShift arbitrary UID + root group: allow writing conf.d/cache/run when not using emptyDir (e.g. plain docker).
RUN chgrp -R 0 /var/cache/nginx /var/run /etc/nginx/conf.d \
    && chmod -R g=u /var/cache/nginx /var/run /etc/nginx/conf.d
ENV API_HOST=api
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
