FROM node:22-slim AS builder

WORKDIR /app

COPY package.json tsconfig.json next.config.mjs postcss.config.mjs eslint.config.mjs prettier.config.mjs ./
COPY messages ./messages
COPY public ./public
COPY src ./src

RUN npm install
RUN npm run build

FROM node:22-slim AS runner

WORKDIR /app

ENV NODE_ENV=production     PORT=3000

RUN groupadd -g 1000 appgroup &&     useradd -u 1000 -g appgroup -s /bin/sh -m appuser

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 3000

CMD ["npm", "run", "start"]
