package com.asml.analytics.facade.controller;

import com.asml.analytics.facade.client.DownstreamClientException;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public final class DownstreamExceptionHandler {
    @ExceptionHandler(DownstreamClientException.class)
    public ResponseEntity<Map<String, Object>> downstream(
            DownstreamClientException error) {
        return ResponseEntity.status(error.statusCode()).body(Map.of(
                "code", "DOWNSTREAM_SERVICE_ERROR",
                "message", error.getMessage()));
    }
}
