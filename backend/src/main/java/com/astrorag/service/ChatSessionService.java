package com.astrorag.service;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ChatSessionService {

    private final ConcurrentHashMap<String, List<Exchange>> sessions = new ConcurrentHashMap<>();

    public void addExchange(String sessionId, String question, String answer) {
        sessions.computeIfAbsent(sessionId, k -> new ArrayList<>())
                .add(new Exchange(question, answer));

        if (sessions.get(sessionId).size() > 20) {
            sessions.get(sessionId).remove(0);
        }
    }

    public String getHistory(String sessionId) {
        List<Exchange> history = sessions.get(sessionId);
        if (history == null || history.isEmpty()) {
            return "";
        }

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < history.size(); i++) {
            Exchange e = history.get(i);
            sb.append("Q").append(i + 1).append(": ").append(e.question()).append("\n");
            sb.append("A").append(i + 1).append(": ").append(e.answer()).append("\n\n");
        }
        return sb.toString().trim();
    }

    public List<Map<String, String>> getHistoryList(String sessionId) {
        List<Exchange> history = sessions.get(sessionId);
        if (history == null) {
            return List.of();
        }
        return history.stream()
                .map(e -> Map.of("question", e.question(), "answer", e.answer()))
                .toList();
    }

    public void clear(String sessionId) {
        sessions.remove(sessionId);
    }

    private record Exchange(String question, String answer) {
    }
}
