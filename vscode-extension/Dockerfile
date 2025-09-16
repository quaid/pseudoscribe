# VSCode Extension Testing Container
FROM node:18

WORKDIR /app

# Install system dependencies for VSCode testing
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    libgtk-3-0 \
    libnss3 \
    libasound2 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libpango-1.0-0 \
    libgbm1 \
    git \
    python3 \
    make \
    g++ \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

# Copy the test script
COPY run-tests.sh /app/run-tests.sh

RUN chmod +x /app/run-tests.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD npm run compile || exit 1

# Default command
CMD ["/app/run-tests.sh"]
