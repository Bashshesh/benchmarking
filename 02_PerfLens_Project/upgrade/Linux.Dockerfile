ARG JAVA_IMAGE=perflens-jmh845:prepared
FROM ${JAVA_IMAGE} AS java
FROM python:3.12.12-slim-bookworm
COPY --from=java /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk PATH=/opt/java/openjdk/bin:$PATH PYTHONDONTWRITEBYTECODE=1
COPY requirements-lock.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
USER 10001:10001
WORKDIR /out
