package com.analytics.agent.config;

import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.security.keyvault.secrets.SecretClient;
import com.azure.security.keyvault.secrets.SecretClientBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Resolves the gateway credential from the Key Vault behind Databricks secret
 * scope
 * lis-analytics-15528, so the key is never stored on disk or in the
 * environment.
 */
@Component
public class AsmlApiKeyProvider {

    private final String apiKey;

    public AsmlApiKeyProvider(@Value("${asml.ai.key-vault-url}") String keyVaultUrl,
            @Value("${asml.ai.secret-name}") String secretName) {

        SecretClient client = new SecretClientBuilder()
                .vaultUrl(keyVaultUrl)
                // Picks up the local `az login` session, or a managed identity when deployed
                .credential(new DefaultAzureCredentialBuilder().build())
                .buildClient();

        this.apiKey = client.getSecret(secretName).getValue();
    }

    public String get() {
        return apiKey;
    }
}
