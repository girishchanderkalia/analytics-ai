package com.asml.analytics.facade.client;
import static org.assertj.core.api.Assertions.assertThat;
import java.lang.reflect.Method;
import org.junit.jupiter.api.Test;
class ClientRouteContractTest {
    @Test void clientsAreSeparatedByInterface(){
        assertThat(methodNames(RuntimeServiceClient.class)).containsExactlyInAnyOrder("chat","resume","getConversation");
        assertThat(methodNames(AnalyticsFoundationClient.class)).contains("queryTrends","getDistribution","createWorkspace","queryWafers");
    }
    private static String[] methodNames(Class<?> type){return java.util.Arrays.stream(type.getDeclaredMethods()).map(Method::getName).toArray(String[]::new);}
}
