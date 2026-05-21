package com.astrorag.controller;

import com.astrorag.model.ChatRequest;
import com.astrorag.model.SourceReference;
import com.astrorag.service.ChatSessionService;
import com.astrorag.service.RagService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

@RestController
@CrossOrigin(origins = "*")
public class ChatController {

    private final RagService ragService;
    private final ChatSessionService sessionService;

    public ChatController(RagService ragService, ChatSessionService sessionService) {
        this.ragService = ragService;
        this.sessionService = sessionService;
    }

    @PostMapping(value = "/api/chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chat(@RequestBody ChatRequest request) {
        String sessionId = request.sessionId() != null && !request.sessionId().isBlank()
                ? request.sessionId()
                : UUID.randomUUID().toString();

        SseEmitter emitter = new SseEmitter(180000L);

        CompletableFuture.runAsync(() -> {
            try {
                emitter.send(SseEmitter.event().name("session").data(sessionId));
            } catch (IOException e) {
                emitter.completeWithError(e);
                return;
            }

            ragService.query(
                    request.question(),
                    sessionId,
                    token -> {
                        try {
                            emitter.send(SseEmitter.event().name("token").data(token));
                        } catch (IOException e) {
                            emitter.completeWithError(e);
                        }
                    },
                    sources -> {
                        try {
                            emitter.send(SseEmitter.event().name("sources").data(sources));
                        } catch (IOException e) {
                            emitter.completeWithError(e);
                        }
                    },
                    () -> {
                        try {
                            emitter.send(SseEmitter.event().name("done").data("complete"));
                            emitter.complete();
                        } catch (IOException e) {
                            emitter.completeWithError(e);
                        }
                    },
                    error -> emitter.completeWithError(error)
            );
        });

        return emitter;
    }

    @GetMapping("/api/chat/{sessionId}/history")
    public List<Map<String, String>> getHistory(@PathVariable String sessionId) {
        return sessionService.getHistoryList(sessionId);
    }

    @DeleteMapping("/api/chat/{sessionId}")
    public Map<String, String> clearSession(@PathVariable String sessionId) {
        sessionService.clear(sessionId);
        return Map.of("status", "ok", "message", "会话已清除");
    }
}
