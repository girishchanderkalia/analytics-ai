package com.asml.analytics.facade.dto;

import java.util.List;

/**
 * DTO shape mirrors
 * contracts/workflow-runtime-api/openapi.yaml#/components/schemas/TrendSeries.
 * Hand-written here; a real build should generate this from the OpenAPI spec
 * (see app-ui-service/README.md) instead of maintaining it by hand.
 */
public class TrendSeries {

    private String machine;
    private String product;
    private String lotId;
    private String layerId;
    private String exposureEquipmentId;
    private List<TrendPoint> points;

    public String getMachine() {
        return machine;
    }

    public void setMachine(String machine) {
        this.machine = machine;
    }

    public String getProduct() {
        return product;
    }

    public void setProduct(String product) {
        this.product = product;
    }

    public String getLotId() {
        return lotId;
    }

    public void setLotId(String lotId) {
        this.lotId = lotId;
    }

    public String getLayerId() {
        return layerId;
    }

    public void setLayerId(String layerId) {
        this.layerId = layerId;
    }

    public String getExposureEquipmentId() {
        return exposureEquipmentId;
    }

    public void setExposureEquipmentId(String exposureEquipmentId) {
        this.exposureEquipmentId = exposureEquipmentId;
    }

    public List<TrendPoint> getPoints() {
        return points;
    }

    public void setPoints(List<TrendPoint> points) {
        this.points = points;
    }

    public static class TrendPoint {
        private String date;
        private double kpiValue;
        private String lotId;

        public String getDate() {
            return date;
        }

        public void setDate(String date) {
            this.date = date;
        }

        public double getKpiValue() {
            return kpiValue;
        }

        public void setKpiValue(double kpiValue) {
            this.kpiValue = kpiValue;
        }

        public String getLotId() {
            return lotId;
        }

        public void setLotId(String lotId) {
            this.lotId = lotId;
        }
    }
}
