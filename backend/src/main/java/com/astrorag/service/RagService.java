package com.astrorag.service;

import com.astrorag.model.SourceReference;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.ChatMessage;
import dev.langchain4j.data.message.SystemMessage;
import dev.langchain4j.data.message.UserMessage;
import dev.langchain4j.model.StreamingResponseHandler;
import dev.langchain4j.model.openai.OpenAiStreamingChatModel;
import dev.langchain4j.model.output.Response;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

@Service
public class RagService {

    private static final String SYSTEM_PROMPT = """
            你是一位资深天文学专家，精通深空天体（星云、星团、星系）、星座、恒星演化、宇宙学等天文知识。
            请根据以下参考资料回答用户问题。
            - 如果参考资料包含答案，请给出详细、准确的回答，并提及使用的是哪条参考资料。
            - 如果参考资料不完整，可以结合你的天文知识补充，但要明确说明哪些来自资料、哪些来自你的知识。
            - 如果参考资料完全不包含答案，请诚实告知，不要编造。可以给出一般性的天文知识建议。
            - 回答时请用流畅自然的中文，适当使用天文术语。
            """;

    private static final String PROMPT_TEMPLATE = """
            参考资料：
            %s

            ---
            对话历史：
            %s

            ---
            用户问题：%s
            """;

    private final RestClient restClient;
    private final OpenAiStreamingChatModel streamingChatModel;
    private final ChatSessionService sessionService;

    public RagService(RestClient.Builder restClientBuilder,
                      OpenAiStreamingChatModel streamingChatModel,
                      ChatSessionService sessionService,
                      @Value("${astrorag.embedding.base-url}") String embeddingBaseUrl) {
        this.restClient = restClientBuilder.baseUrl(embeddingBaseUrl).build();
        this.streamingChatModel = streamingChatModel;
        this.sessionService = sessionService;
    }

    public void query(String question, String sessionId,
                      Consumer<String> onToken,
                      Consumer<List<SourceReference>> onSources,
                      Runnable onComplete,
                      Consumer<Throwable> onError) {

        // 调用 embedding 服务器的 /v1/search 检索
        Map<String, Object> searchBody = Map.of("query", question, "top_k", 5);
        Map<String, Object> searchResp = restClient.post()
                .uri("/v1/search")
                .body(searchBody)
                .retrieve()
                .body(new ParameterizedTypeReference<>() {});

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> rawResults = (List<Map<String, Object>>) searchResp.get("results");

        List<SourceReference> sources = new ArrayList<>();
        StringBuilder contextBuilder = new StringBuilder();

        if (rawResults != null) {
            for (int i = 0; i < rawResults.size(); i++) {
                Map<String, Object> r = rawResults.get(i);
                String document = (String) r.get("document");
                @SuppressWarnings("unchecked")
                Map<String, Object> metadata = (Map<String, Object>) r.get("metadata");
                double score = ((Number) r.get("score")).doubleValue();

                String title = metadata != null ? (String) metadata.getOrDefault("name", "未知") : "未知";

                sources.add(new SourceReference(title, document, Math.round(score * 1000.0) / 1000.0));

                contextBuilder.append("[").append(i + 1).append("] ");
                contextBuilder.append(document);
                contextBuilder.append("\n\n");
            }
        }

        onSources.accept(sources);

        String chatHistory = sessionService.getHistory(sessionId);
        String userPrompt = String.format(PROMPT_TEMPLATE,
                contextBuilder.toString(),
                chatHistory.isBlank() ? "（无历史对话）" : chatHistory,
                question);

        List<ChatMessage> messages = List.of(
                SystemMessage.from(SYSTEM_PROMPT),
                UserMessage.from(userPrompt)
        );

        StringBuilder fullAnswer = new StringBuilder();

        streamingChatModel.generate(messages, new StreamingResponseHandler<>() {
            @Override
            public void onNext(String token) {
                if (token != null && !token.isEmpty()) {
                    fullAnswer.append(token);
                    onToken.accept(token);
                }
            }

            @Override
            public void onComplete(Response<AiMessage> response) {
                sessionService.addExchange(sessionId, question, fullAnswer.toString());
                onComplete.run();
            }

            @Override
            public void onError(Throwable error) {
                onError.accept(error);
            }
        });
    }
}
