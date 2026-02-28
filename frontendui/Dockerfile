# ─────────────────────────────────────────────────────────────
# Conut Ops AI  –  Frontend (React + Vite)
# Build: docker build -t conut-frontend ./frontendui
# ─────────────────────────────────────────────────────────────

# ── Stage 1: build the React app ─────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY package.json package-lock.json ./

RUN npm ci --prefer-offline

# Copy source and build
COPY . .

# Inject the backend URL at build time (can be overridden by --build-arg)
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build


# ── Stage 2: serve with Nginx ─────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove default Nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config: serve SPA, proxy /api → backend
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
