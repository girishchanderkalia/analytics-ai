# Build context MUST be the app-ui-service/ folder itself:
#   cd ai-enabled-analytics-v2/app-ui-service
#   mvn clean package
#   docker build -t iact/app-ui-service:latest .
#
# Single-stage on purpose, mirroring the repo's standard image pattern (build
# the jar on the host with Maven first, then just package it) rather than a
# multi-stage Maven-in-Docker build.
FROM eclipse-temurin:8-jre-jammy

WORKDIR /app
COPY target/app-ui-service-*.jar app.jar

EXPOSE 8090
ENV WORKFLOWRUNTIME_BASEURL=http://analytics-workflow-runtime:8100
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
