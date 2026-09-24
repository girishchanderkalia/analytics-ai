package com.asml.analytics.facade.client;

public final class DownstreamClientException extends RuntimeException {
    private final int statusCode;

    public DownstreamClientException(String message, int statusCode) {
        super(message);
        this.statusCode = statusCode;
    }

    public DownstreamClientException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 502;
    }

    public int statusCode() {
        return statusCode;
    }
}
