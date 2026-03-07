FROM node:22-alpine AS base
WORKDIR /app
RUN npm install -g npm@11.10.0

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
ARG VITE_API_ORIGIN=http://localhost:8000
ARG VITE_API_BASE_PATH=/v1
ENV VITE_API_ORIGIN=${VITE_API_ORIGIN}
ENV VITE_API_BASE_PATH=${VITE_API_BASE_PATH}
COPY --from=deps /app/node_modules /app/node_modules
COPY . .
RUN npm run build

FROM base AS production
WORKDIR /app
ARG VITE_API_ORIGIN=http://localhost:8000
ARG VITE_API_BASE_PATH=/v1
ENV NODE_ENV=production
ENV VITE_API_ORIGIN=${VITE_API_ORIGIN}
ENV VITE_API_BASE_PATH=${VITE_API_BASE_PATH}
RUN npm install -g serve@14.2.4
COPY --from=builder /app/dist /app/dist
EXPOSE 3000
CMD ["sh", "-c", "serve -s dist -l ${PORT:-3000}"]
