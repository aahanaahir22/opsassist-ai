FROM grafana/grafana:11.5.2

COPY infra/grafana/provisioning/dashboards/opsassist.yml /etc/grafana/provisioning/dashboards/opsassist.yml
COPY infra/railway/grafana-datasource.yml /etc/grafana/provisioning/datasources/prometheus.yml
COPY infra/grafana/dashboards/opsassist-overview.json /var/lib/grafana/dashboards/opsassist-overview.json

ENV GF_USERS_ALLOW_SIGN_UP=false
EXPOSE 3000
