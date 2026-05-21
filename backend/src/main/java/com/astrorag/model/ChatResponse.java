package com.astrorag.model;

import java.util.List;

public record ChatResponse(String answer, List<SourceReference> sources) {
}
