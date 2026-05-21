package com.astrorag.config;

import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.model.openai.OpenAiStreamingChatModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

@Configuration
public class LangChain4jConfig {

    @Value("${langchain4j.lmstudio.base-url}")
    private String lmStudioBaseUrl;

    @Value("${langchain4j.lmstudio.chat-model}")
    private String chatModelName;

    @Value("${langchain4j.lmstudio.chat-timeout}")
    private long chatTimeout;

    @Bean
    public OpenAiChatModel chatModel() {
        return OpenAiChatModel.builder()
                .baseUrl(lmStudioBaseUrl)
                .apiKey("lm-studio")
                .modelName(chatModelName)
                .timeout(Duration.ofSeconds(chatTimeout))
                .temperature(0.7)
                .build();
    }

    @Bean
    public OpenAiStreamingChatModel streamingChatModel() {
        return OpenAiStreamingChatModel.builder()
                .baseUrl(lmStudioBaseUrl)
                .apiKey("lm-studio")
                .modelName(chatModelName)
                .timeout(Duration.ofSeconds(chatTimeout))
                .temperature(0.7)
                .build();
    }
}
