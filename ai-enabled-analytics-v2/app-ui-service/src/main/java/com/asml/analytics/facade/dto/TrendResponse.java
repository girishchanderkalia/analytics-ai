package com.asml.analytics.facade.dto;

import java.util.List;

/** Response of GET /trends, per contracts/workflow-runtime-api/openapi.yaml. */
public class TrendResponse {

    private List<TrendSeries> series;

    public List<TrendSeries> getSeries() {
        return series;
    }

    public void setSeries(List<TrendSeries> series) {
        this.series = series;
    }
}
