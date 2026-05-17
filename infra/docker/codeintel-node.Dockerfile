FROM node:20-alpine

RUN apk add --no-cache tini \
 && npm install -g --omit=dev \
      jest@29.7.0 \
      ts-jest@29.2.5 \
      typescript@5.6.2 \
      jest-junit@16.0.0

# node:20-alpine already reserves uid 1000 for the `node` user; reuse it
# instead of creating a conflicting uid.
USER node
WORKDIR /repo

ENTRYPOINT ["/sbin/tini", "--", "npx", "jest"]
