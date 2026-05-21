package com.astrorag.model;

import java.util.List;
import java.util.Map;

public record SearchResult(String id, String document, Map<String, Object> metadata, double score) {
}
