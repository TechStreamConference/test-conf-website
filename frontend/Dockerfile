FROM node:22-slim AS builder

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm build

# `adapter-node` does not include packages from `dependencies` in the build output.
# Keep the production packages here so the `COPY` commands below can add them to the final image.
RUN pnpm prune --prod

FROM node:22-slim

WORKDIR /app

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/build ./build

ENV PORT=3000
EXPOSE 3000

CMD ["node", "build/index.js"]
