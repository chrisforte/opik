package com.comet.opik.api.evaluators;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

import java.beans.ConstructorProperties;
import java.util.UUID;

import static com.comet.opik.api.evaluators.AutomationRuleEvaluatorUserDefinedMetricPython.UserDefinedMetricPythonCode;

@SuperBuilder(toBuilder = true)
@EqualsAndHashCode(callSuper = true)
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public final class AutomationRuleEvaluatorUpdateUserDefinedMetricPython
        extends
            AutomationRuleEvaluatorUpdate<UserDefinedMetricPythonCode> {

    @ConstructorProperties({"name", "samplingRate", "enabled", "code", "projectId"})
    public AutomationRuleEvaluatorUpdateUserDefinedMetricPython(
            @NotBlank String name, float samplingRate, boolean enabled, @NotNull UserDefinedMetricPythonCode code,
            @NotNull UUID projectId) {
        super(name, samplingRate, enabled, code, projectId);
    }

    /**
     * Two purposes:
     * - Makes the polymorphic T code available for serialization.
     * - Provides the specific type T for Open API and Fern.
     */
    @JsonProperty
    @Override
    public UserDefinedMetricPythonCode getCode() {
        return super.getCode();
    }

    @Override
    public AutomationRuleEvaluatorType getType() {
        return AutomationRuleEvaluatorType.USER_DEFINED_METRIC_PYTHON;
    }
}
