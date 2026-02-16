FROM node:22-alpine AS base
WORKDIR /app
RUN npm install -g npm@11.10.0

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_ORIGIN=
ARG NEXT_PUBLIC_API_BASE_PATH=/api
ENV NEXT_PUBLIC_API_ORIGIN=${NEXT_PUBLIC_API_ORIGIN}
ENV NEXT_PUBLIC_API_BASE_PATH=${NEXT_PUBLIC_API_BASE_PATH}
COPY --from=deps /app/node_modules /app/node_modules
COPY . ./
RUN npm run build

FROM base AS production
WORKDIR /app
ARG NEXT_PUBLIC_API_ORIGIN=
ARG NEXT_PUBLIC_API_BASE_PATH=/api
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_ORIGIN=${NEXT_PUBLIC_API_ORIGIN}
ENV NEXT_PUBLIC_API_BASE_PATH=${NEXT_PUBLIC_API_BASE_PATH}
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/.next /app/.next
COPY --from=builder /app/public /app/public
COPY --from=builder /app/next.config.ts /app/next.config.ts
CMD ["npm", "start"]
