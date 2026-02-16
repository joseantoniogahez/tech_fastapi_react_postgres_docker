FROM node:22-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_ORIGIN=
ARG NEXT_PUBLIC_API_BASE_PATH=/api
ENV NEXT_PUBLIC_API_ORIGIN=${NEXT_PUBLIC_API_ORIGIN}
ENV NEXT_PUBLIC_API_BASE_PATH=${NEXT_PUBLIC_API_BASE_PATH}
COPY package.json package-lock.json ./
RUN npm install
COPY . ./
RUN npm run build

FROM node:22-alpine AS production
WORKDIR /app
ARG NEXT_PUBLIC_API_ORIGIN=
ARG NEXT_PUBLIC_API_BASE_PATH=/api
COPY package.json package-lock.json ./
COPY --from=builder /app/.next /app/.next
COPY --from=builder /app/public /app/public
COPY --from=builder /app/node_modules /app/node_modules
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_ORIGIN=${NEXT_PUBLIC_API_ORIGIN}
ENV NEXT_PUBLIC_API_BASE_PATH=${NEXT_PUBLIC_API_BASE_PATH}
CMD ["npm", "start"]
