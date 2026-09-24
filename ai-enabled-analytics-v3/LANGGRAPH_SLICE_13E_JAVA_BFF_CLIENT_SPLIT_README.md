# Slice 13E: Java BFF client split

Separates downstream calls into:

- `RuntimeServiceClient`: chat, resume and conversation retrieval.
- `AnalyticsFoundationClient`: deterministic Foundation operations.

## JDK requirement

All builds use:

```text
C:\Program Files\Java\jdk-25.0.1
```

## Test

```bash
export JAVA_HOME='C:\Program Files\Java\jdk-25.0.1'
export PATH="/c/Program Files/Java/jdk-25.0.1/bin:$PATH"
export MAVEN_OPTS='-Djavax.net.ssl.trustStoreType=Windows-ROOT -Djavax.net.ssl.trustStore=NONE'

cd app-ui/opo-monitoring
mvn -U -s "$HOME/.m2/settings.xml" clean test
```
