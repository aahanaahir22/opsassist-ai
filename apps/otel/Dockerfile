FROM otel/opentelemetry-collector-contrib:0.120.0

COPY infra/otel-collector.yaml /etc/otelcol-contrib/config.yaml

EXPOSE 4317 4318 8889
CMD ["--config=/etc/otelcol-contrib/config.yaml"]
