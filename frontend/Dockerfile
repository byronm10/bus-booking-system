FROM --platform=linux/arm64 public.ecr.aws/docker/library/node:lts-slim

WORKDIR /app

ENV NODE_ENV=production \
    PATH="/app/node_modules/.bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json ./
RUN npm ci --only=production

COPY . .

RUN npm run build

RUN npm install -g serve

HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000

RUN echo '#!/bin/bash' > /start.sh && \
    echo 'set -ex' >> /start.sh && \
    echo 'echo "Node version: $(/usr/local/bin/node --version)"' >> /start.sh && \
    echo 'echo "NPM version: $(/usr/local/bin/npm --version)"' >> /start.sh && \
    echo 'echo "Current directory: $(pwd)"' >> /start.sh && \
    echo 'echo "App directory contents:"' >> /start.sh && \
    echo 'ls -la /app' >> /start.sh && \
    echo 'echo "Build directory contents:"' >> /start.sh && \
    echo 'ls -la /app/build' >> /start.sh && \
    echo 'exec /usr/local/bin/serve -s build -l 3000' >> /start.sh && \
    chmod +x /start.sh

ENTRYPOINT ["/start.sh"]