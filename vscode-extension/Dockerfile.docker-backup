# VSCode Extension Testing Container
FROM node:18-alpine

WORKDIR /app

# Install system dependencies for VSCode testing
RUN apk add --no-cache \
    xvfb \
    gtk+3.0 \
    nss \
    alsa-lib \
    at-spi2-atk \
    cups-libs \
    drm \
    gtk+3.0 \
    libxcomposite \
    libxdamage \
    libxrandr \
    libxss \
    libxtst \
    pango \
    git \
    python3 \
    make \
    g++ \
    curl

# Set display for headless testing
ENV DISPLAY=:99

# Copy package files
COPY package*.json tsconfig.json .eslintrc.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY src/ ./src/

# Build the extension
RUN npm run compile

# Create test script
RUN echo '#!/bin/sh\n\
set -e\n\
echo "Starting Xvfb..."\n\
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &\n\
sleep 2\n\
echo "Running extension tests..."\n\
npm test\n\
echo "Tests completed successfully"' > /app/run-tests.sh

RUN chmod +x /app/run-tests.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD npm run compile || exit 1

# Default command
CMD ["/app/run-tests.sh"]
