FROM node:22.23.1-alpine AS base
WORKDIR /app
RUN npm install -g npm@12.0.1

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
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
ENV NODE_ENV=production
ENV NO_UPDATE_CHECK=1
RUN npm install -g serve@14.2.6
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/.generated/serve.json /app/serve.json
EXPOSE 3000
CMD ["sh", "-c", "serve -s dist -l ${PORT:-3000} -c /app/serve.json"]
