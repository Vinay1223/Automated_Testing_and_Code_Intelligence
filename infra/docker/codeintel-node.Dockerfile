FROM node:20-alpine

RUN apk add --no-cache tini \
 && npm install -g --omit=dev \
      jest@29.7.0 \
      ts-jest@29.2.5 \
      typescript@5.6.2 \
      jest-junit@16.0.0

RUN addgroup -g 1000 sandbox && adduser -D -u 1000 -G sandbox sandbox
USER sandbox
WORKDIR /repo

ENTRYPOINT ["/sbin/tini", "--", "npx", "jest"]
