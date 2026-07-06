FROM node:22-slim AS builder

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm build

FROM node:22-slim

WORKDIR /app

COPY --from=builder /app/build ./build

ENV PORT=3000
EXPOSE 3000

CMD ["node", "build/index.js"]
