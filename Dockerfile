# ──────────────────────────────────────────────────────────────
# PyFlink — Apache Flink 1.19 + Python 3.10
# Connectors: Kafka | Iceberg | S3/MinIO | Nessie | Prometheus
# ──────────────────────────────────────────────────────────────
FROM apache/flink:1.19.0-scala_2.12-java11

USER root

# ── Python 3.10 ───────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.10 \
        python3.10-dev \
        python3-pip \
        curl \
        wget \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.10 /usr/bin/python

# ── Connector JARs ────────────────────────────────────────────
ENV FLINK_HOME=/opt/flink
ENV FLINK_LIB=$FLINK_HOME/lib

# Kafka SQL connector — 3.3.0-1.19 is the correct version for Flink 1.19
RUN wget -q -O $FLINK_LIB/flink-sql-connector-kafka-3.3.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.19/flink-sql-connector-kafka-3.3.0-1.19.jar

# Iceberg Flink runtime — 1.7.1 is the correct version for Flink 1.19
RUN wget -q -O $FLINK_LIB/iceberg-flink-runtime-1.19-1.7.1.jar \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.19/1.7.1/iceberg-flink-runtime-1.19-1.7.1.jar

# S3 / MinIO plugin
RUN wget -q -O $FLINK_LIB/flink-s3-fs-hadoop-1.19.0.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-s3-fs-hadoop/1.19.0/flink-s3-fs-hadoop-1.19.0.jar

# Nessie catalog — must match Iceberg version
RUN wget -q -O $FLINK_LIB/iceberg-nessie-1.7.1.jar \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-nessie/1.7.1/iceberg-nessie-1.7.1.jar

# Prometheus metrics reporter
RUN wget -q -O $FLINK_LIB/flink-metrics-prometheus-1.19.0.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-metrics-prometheus/1.19.0/flink-metrics-prometheus-1.19.0.jar

# ── Python packages ───────────────────────────────────────────
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ── Flink config: MinIO + Prometheus ─────────────────────────
RUN echo "s3.endpoint: http://minio:9000"        >> $FLINK_HOME/conf/flink-conf.yaml && \
    echo "s3.path-style-access: true"            >> $FLINK_HOME/conf/flink-conf.yaml && \
    echo "s3.access-key: minioadmin"             >> $FLINK_HOME/conf/flink-conf.yaml && \
    echo "s3.secret-key: minioadmin123"          >> $FLINK_HOME/conf/flink-conf.yaml && \
    echo "metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory" >> $FLINK_HOME/conf/flink-conf.yaml && \
    echo "metrics.reporter.prom.port: 9249"      >> $FLINK_HOME/conf/flink-conf.yaml

ENV PYFLINK_PYTHON=/usr/bin/python3

WORKDIR /opt/flink/jobs

USER flink
