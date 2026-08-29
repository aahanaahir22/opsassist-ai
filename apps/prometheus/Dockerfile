FROM prom/prometheus:v3.2.1

COPY infra/railway/prometheus.yml /etc/prometheus/prometheus.yml
COPY infra/prometheus/alerts.yml /etc/prometheus/alerts.yml

EXPOSE 9090
CMD ["--config.file=/etc/prometheus/prometheus.yml", "--storage.tsdb.retention.time=15d", "--storage.tsdb.path=/prometheus"]
