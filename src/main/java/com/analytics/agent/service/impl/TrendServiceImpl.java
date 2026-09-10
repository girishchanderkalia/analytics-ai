package com.analytics.agent.service.impl;

import com.analytics.agent.model.Outlier;
import com.analytics.agent.model.TrendResponse;
import com.analytics.agent.service.TrendService;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TrendServiceImpl implements TrendService {

    @Override
    public TrendResponse getTrends() {
        return new TrendResponse(List.of(
            new Outlier("NXE3600", "ProductA", 15.0),
            new Outlier("NXE3400", "ProductB", 8.5),
            new Outlier("NXT1970", "ProductC", 4.2)
        ));
    }
}
