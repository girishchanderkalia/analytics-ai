# Slice 13C compile correction

Replaces the single nested `FoundationDtos` container with top-level public DTO records and aligns the Analytics Foundation client plus deterministic controllers.

After extraction, remove the obsolete file:

`app-ui/opo-monitoring/src/main/java/com/asml/analytics/facade/dto/foundation/FoundationDtos.java`

Then run `mvn -s "$HOME/.m2/settings.xml" -U clean test` from `app-ui/opo-monitoring`.
