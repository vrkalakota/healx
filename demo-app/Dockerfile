FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY leaky-app.go .
RUN go build -o leaky-app leaky-app.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/leaky-app .
EXPOSE 8080
CMD ["./leaky-app"]