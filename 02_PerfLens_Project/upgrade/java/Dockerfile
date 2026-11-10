FROM maven:3.9.9-eclipse-temurin-21
COPY dependencies-pom.xml /harness/dependencies-pom.xml
RUN mvn -B -f /harness/dependencies-pom.xml org.apache.maven.plugins:maven-dependency-plugin:3.8.1:copy-dependencies -DoutputDirectory=/opt/jmh
COPY src /harness/src
COPY build-roaring.sh /harness/build-roaring.sh
RUN sed -i 's/\r$//' /harness/build-roaring.sh && chmod 755 /harness/build-roaring.sh && mkdir -p /out /src
USER 10001:10001
WORKDIR /out
ENTRYPOINT []
