#!/bin/sh
set -eu

: "${DEPLOYMENT_ENVIRONMENT:=prd}"
export DEPLOYMENT_ENVIRONMENT

envsubst '${DEPLOYMENT_ENVIRONMENT}' \
  < /etc/wkpoule/runtime-config.js.template \
  > /usr/share/nginx/html/runtime-config.js
