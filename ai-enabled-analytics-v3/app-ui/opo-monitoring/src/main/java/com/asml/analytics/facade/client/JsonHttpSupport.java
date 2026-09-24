package com.asml.analytics.facade.client;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

final class JsonHttpSupport {
    private final HttpClient client;
    private final ObjectMapper mapper;
    private final String baseUrl;
    private final Duration readTimeout;

    JsonHttpSupport(
            HttpClient client,
            ObjectMapper mapper,
            String baseUrl,
            Duration readTimeout) {
        this.client = client;
        this.mapper = mapper;
        this.baseUrl = baseUrl;
        this.readTimeout = readTimeout;
    }

    <T> T get(String path, Class<T> responseType) {
        return exchange("GET", path, null, responseType);
    }

    <T> T post(String path, Object body, Class<T> responseType) {
        return exchange("POST", path, body, responseType);
    }

    private <T> T exchange(
            String method,
            String path,
            Object body,
            Class<T> responseType) {
        try {
            HttpRequest.Builder request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + path))
                    .timeout(readTimeout)
                    .header("Accept", "application/json");
            if (body == null) {
                request.method(
                        method,
                        HttpRequest.BodyPublishers.noBody());
            } else {
                request.header("Content-Type", "application/json")
                        .method(
                                method,
                                HttpRequest.BodyPublishers.ofString(
                                        mapper.writeValueAsString(body)));
            }
            HttpResponse<String> response = client.send(
                    request.build(),
                    HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new DownstreamClientException(
                        "Downstream call failed: " + method + " " + path,
                        response.statusCode());
            }
            return mapper.readValue(response.body(), responseType);
        } catch (DownstreamClientException error) {
            throw error;
        } catch (JsonProcessingException error) {
            throw new DownstreamClientException(
                    "Invalid downstream JSON response for " + method + " " + path,
                    error);
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new DownstreamClientException(
                    "Downstream call was interrupted",
                    error);
        } catch (IOException | IllegalArgumentException error) {
            throw new DownstreamClientException(
                    "Downstream call failed: " + method + " " + path,
                    error);
        }
    }
}
