package com.asml.analytics.facade.dto;

import java.util.HashMap;
import java.util.Map;

/**
 * Filters applied to a workspace, per WorkspaceService.addFilters()
 * (.github/copilot-instructions.md `## 8`). Backed by a plain map so it can
 * carry any of the application's filter keys (machine, product, lot_id, ...)
 * without the facade hard-coding OPO-specific field names.
 */
public class Filters {

    private final Map<String, Object> values = new HashMap<>();

    public Map<String, Object> getValues() {
        return values;
    }

    public void put(String key, Object value) {
        values.put(key, value);
    }
}
