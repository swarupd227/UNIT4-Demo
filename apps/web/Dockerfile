FROM node:22-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# A missing recording should stop the build, not surface on stage.
RUN test "$(ls public/fallback/*.webm 2>/dev/null | wc -l)" -eq 9 \
    || (echo "Expected 9 scene recordings. Run npm run record first." >&2 && exit 1)
RUN npm run build

# Runs as a non-root user on port 8080. API_UPSTREAM is written into the template at startup.
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY nginx/security-headers.conf /etc/nginx/security-headers.conf
COPY --from=build /web/dist /usr/share/nginx/html
