#!/bin/sh
set -e

# Replace placeholder with actual environment variable value
# Default to empty string if REACT_APP_API_URL is not set
API_URL="${REACT_APP_API_URL:-}"

if [ -n "$API_URL" ]; then
  echo "Injecting REACT_APP_API_URL=$API_URL into env-config.js"
  sed -i "s|PLACEHOLDER_API_URL|$API_URL|g" /usr/share/nginx/html/env-config.js
else
  echo "Warning: REACT_APP_API_URL not set, keeping placeholder"
fi

# Start nginx
exec nginx -g 'daemon off;'
