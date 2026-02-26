# Enterprise Test Harness Automation Guide

**Date**: February 6, 2026
**Purpose**: Knowledge base for building enterprise-level automation testing systems
**Scope**: AI Assistant skill classification and agent workflows

---

## Overview

This document captures knowledge extracted from implementing automation testing for the skill-level intent detection system. It provides guidance for automating test harnesses at enterprise scale.

---

## 1. AIAI 4-Tier Testing Framework

The official AIAI testing framework defines four tiers of testing:

```
+------------------+     +--------------------+     +----------------+     +------------------+
|   UNIT TESTS     | --> | INTEGRATION TESTS  | --> | QUALITY TESTS  | --> | PERFORMANCE TESTS|
|   (Isolated)     |     | (Deployed Sandbox) |     | (MLFlow)       |     | (JMeter)         |
+------------------+     +--------------------+     +----------------+     +------------------+
     |                         |                          |                       |
     v                         v                          v                       v
  Mocked LLM              Real LLM                   Metrics Logging        Load Testing
  Mocked MCP              Real Services              ndcg, precision        Concurrent Users
  Pact Contracts          HTTP Calls                 MLFlow Tracing         Response Times
```

### Tier Descriptions

| Tier | Environment | External Services | When to Run |
|------|-------------|-------------------|-------------|
| Unit | Local/CI | All mocked | Every commit |
| Integration | Deployed sandbox | Real | Pre-release |
| Quality | Deployed sandbox | Real + MLFlow | Scheduled |
| Performance | Deployed sandbox | Real + JMeter | Pre-production |

---

## 2. Contract Testing with Pact IO

### The Pattern

```
                    +------------+
                    |  Contract  |
                    | (Pactflow) |
                    +-----+------+
                          |
            +-------------+-------------+
            |                           |
            v                           v
     +------------+              +------------+
     |  Consumer  |              |  Provider  |
     | (Agent)    |              | (LLM/Tool) |
     +------------+              +------------+
            |                           |
            v                           v
     Unit tests with              Provider verifies
     provider mock                against contract
```

### Implementation for Skill Classifier

**Consumer Contracts** (Skill Classifier expects):
```python
# Example Pact contract definition
from pact import Consumer, Provider

pact = Consumer('SkillClassifier').has_pact_with(Provider('LLMService'))

pact.given(
    'a classification request'
).upon_receiving(
    'a skill classification response'
).with_request(
    method='POST',
    path='/classify',
    body={'prompt': 'Create an assembly', 'context': {}}
).will_respond_with(
    status=200,
    body={
        'skill': 'asmstruct',
        'confidence': Decimal(0.85),
        'reasoning': Like('Matched assembly creation intent')
    }
)
```

**Provider Verification**:
```bash
# Provider verifies it can satisfy consumer expectations
pact-verifier --provider-base-url=http://llm-service \
              --pact-url=./pacts/skillclassifier-llmservice.json
```

### Benefits for Enterprise
1. **Decoupled Testing**: Teams can test independently
2. **Contract Evolution**: Version contracts with breaking change detection
3. **CI/CD Integration**: Fail builds when contracts break
4. **Documentation**: Contracts serve as API documentation

---

## 3. Quality Metrics with MLFlow

### Key Metrics for Skill Classification

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| `ndcg_at_3/mean` | Normalized Discounted Cumulative Gain | How well are alternatives ranked? |
| `ndcg_at_3/p90` | 90th percentile NDCG | Worst-case ranking quality |
| `precision_at_3/mean` | Correct in top 3 / 3 | Are correct skills in top 3? |
| `confidence_mean` | Average classification confidence | Model certainty |
| `accuracy` | Correct / Total | Overall correctness |

### MLFlow Integration Pattern

```python
import mlflow

def run_quality_tests():
    with mlflow.start_run(run_name="skill_classifier_quality"):
        # Log parameters
        mlflow.log_param("model_version", "v1.1.0")
        mlflow.log_param("test_count", 107)

        # Run tests and collect metrics
        results = run_integration_tests()

        # Log metrics
        mlflow.log_metric("accuracy", results["pass_rate"])
        mlflow.log_metric("confidence_mean", results["confidence_stats"]["average"])
        mlflow.log_metric("ndcg_at_3_mean", calculate_ndcg(results))

        # Log artifacts
        mlflow.log_artifact("test_results/integration_test_report.json")

        # Log dataset
        mlflow.log_input(
            mlflow.data.from_json("test_cases.json"),
            context="test_dataset"
        )
```

### Dashboard Queries

From the MLFlow UI (as shown in image (2).png):
- Filter by `metrics.rmse < 1 and params.model = "tree"`
- Group by run name to compare experiments
- Track trends over time for regression detection

---

## 4. LangGraph Tracing for Debugging

### Trace Structure

From the LangGraph UI (as shown in image.png):

```
LangGraph_1
  |-- input_guardrails_1
  |-- agent_1
  |     |-- LangGraph_2
  |     |     |-- load_settings_1
  |     |     |-- __direct_if_input_is_empty
  |     |-- select_language
  |     |-- create_only_question_chain
  |     |     |-- format_inputs
  |     |     |-- RunnableParallel<input,lang>
  |     |     |-- prompt_selector_lang_1
  |     |     |-- ChatMistralAI_1
  |     |     |-- JsonMarkdownOutputParser
  |     |-- load_history
  |     |-- rephrase_query_from_memory
  |-- entity_replacement
  |     |-- LangGraph_3
  |     |-- input_guardrails_2
  |     |-- agent_2
  |           |-- LangGraph_4
  |           |-- retriever
  |                 |-- retrieve_documents_1
```

### Key Trace Elements

1. **Messages Tab**: User input -> Assistant response flow
2. **Inputs/Outputs Tab**: Data at each node
3. **Attributes Tab**: Node configuration
4. **Events Tab**: Timing and execution events

### Enabling Tracing for Tests

```python
from langchain.callbacks import LangChainTracer

tracer = LangChainTracer(project_name="skill_classifier_tests")

async def test_with_tracing():
    result = await classifier.classify(
        prompt="Create assembly",
        callbacks=[tracer]
    )
```

---

## 5. Test Harness Automation Architecture

### Automated Pipeline

```
+----------+     +----------+     +-----------+     +----------+     +---------+
|  Commit  | --> |  Unit    | --> | Deploy    | --> | Integr.  | --> | Quality |
|          |     |  Tests   |     | Sandbox   |     | Tests    |     | Tests   |
+----------+     +----------+     +-----------+     +----------+     +---------+
                      |                                   |               |
                      v                                   v               v
                 Pact Verify                        HTTP Client      MLFlow Log
                 Coverage                           Real LLM         Metrics
```

### Configuration Management

```yaml
# test_config.yaml
environments:
  sandbox:
    url: "${SANDBOX_URL}"
    llm_endpoint: "${AZURE_OPENAI_ENDPOINT}"
    llm_key: "${AZURE_OPENAI_API_KEY}"
    mcp_server: "mcp_server"

test_suites:
  unit:
    markers: ["unit"]
    parallel: true
    max_workers: 4

  integration:
    markers: ["integration"]
    parallel: false  # Sequential for rate limiting
    timeout: 300

  quality:
    markers: ["quality"]
    mlflow_uri: "${MLFLOW_TRACKING_URI}"
    experiment: "skill_classifier"
```

### Regression Detection

```python
def detect_regression(current_results, baseline_results):
    """
    Compare current test results against baseline.
    Flag regressions exceeding threshold.
    """
    regressions = []

    for category, current_stats in current_results["categories"].items():
        baseline_stats = baseline_results["categories"].get(category, {})

        if baseline_stats:
            current_rate = current_stats["pass_rate"]
            baseline_rate = baseline_stats["pass_rate"]

            # Regression threshold: 5% drop
            if current_rate < baseline_rate - 5.0:
                regressions.append({
                    "category": category,
                    "current": current_rate,
                    "baseline": baseline_rate,
                    "delta": current_rate - baseline_rate
                })

    return regressions
```

---

## 6. Enterprise Test Categories for Intent Classification

### Standard Categories (Implemented)

| Code | Name | Purpose | Test Count |
|------|------|---------|------------|
| SSR | Single Skill Routing | Direct intent to skill mapping | 32 |
| CD | Continuation Detection | Short commands in context | 16 |
| ST | Skill Transition | Context switches between skills | 8 |
| AMB | Ambiguous Requests | Unclear intent handling | 16 |
| OOS | Out-of-Scope | Non-domain request rejection | 8 |
| LV | Language Variations | Typos, jargon, informal | 19 |
| MT | Multi-Turn | Full conversation flows | 8 |

### Adversarial Categories (Stress Testing)

| Code | Name | Purpose | Current Pass Rate |
|------|------|---------|-------------------|
| CA | Continuation Abuse | Exploit continuation logic | 40% |
| CONF | Confidence Attacks | Manipulate confidence scores | 50% |
| ADV | Adversarial Inputs | Malicious prompt patterns | 80% |
| CHAOS | Chaos Scenarios | Random/nonsensical input | 100% |
| RF | Rapid Fire | High-frequency requests | 100% |

### Performance Categories (Planned)

| Code | Name | Metric | Target |
|------|------|--------|--------|
| LAT | Latency | P99 response time | <500ms |
| CONC | Concurrency | Users without degradation | 10,000 |
| SOAK | Soak Test | Stability over time | 24 hours |
| SPIKE | Spike Test | Recovery from burst | <30s recovery |

---

## 7. Test Data Management

### Ground Truth Dataset Structure

```json
{
  "version": "1.0.0",
  "created": "2026-02-06",
  "test_cases": [
    {
      "id": "SSR-001",
      "prompt": "Create a car assembly with wheels",
      "expected_skill": "asmstruct",
      "expected_confidence_min": 0.8,
      "tags": ["creation", "direct", "asmstruct"],
      "context": null
    },
    {
      "id": "CD-001",
      "prompt": "yes",
      "expected_skill": "asmstruct",
      "expected_continuation": true,
      "context": {
        "most_recent_skill": "asmstruct"
      }
    }
  ]
}
```

### Dataset Versioning

```
test_data/
  |-- v1.0.0/
  |     |-- ground_truth.json
  |     |-- adversarial.json
  |     |-- edge_cases.json
  |-- v1.1.0/
  |     |-- ground_truth.json  # Added 20 new cases
  |     |-- CHANGELOG.md
  |-- latest -> v1.1.0/
```

---

## 8. CI/CD Integration

### GitHub Actions Example

```yaml
name: Skill Classifier Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest -m unit --cov --junitxml=unit-results.xml

      - name: Verify Pact contracts
        run: pact-verifier --pact-broker-url=${{ secrets.PACT_BROKER_URL }}

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    environment: sandbox
    steps:
      - name: Deploy to sandbox
        run: ./scripts/deploy-sandbox.sh

      - name: Run integration tests
        env:
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
          SANDBOX_URL: ${{ secrets.SANDBOX_URL }}
        run: pytest -m integration --junitxml=integration-results.xml

      - name: Check for regressions
        run: python scripts/check_regression.py --baseline=baseline.json

  quality-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run quality tests with MLFlow
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_URI }}
        run: pytest -m quality --mlflow-experiment=skill_classifier
```

---

## 9. Lessons Learned

### What Works Well

1. **JSON-driven test cases**: Easy to add/modify without code changes
2. **Category-based organization**: Clear separation of test types
3. **Real LLM integration tests**: Closest to production behavior
4. **Confidence thresholds**: Tunable without code changes

### Known Challenges

1. **LLM non-determinism**: Same input can produce different outputs
   - Mitigation: Use confidence ranges, not exact values

2. **Rate limiting**: Real LLM tests hit API limits
   - Mitigation: Sequential execution, retry with backoff

3. **Thread state pollution**: Architectural issue in framework
   - Mitigation: Document as known limitation, propose fix

4. **Test flakiness**: Network issues cause false failures
   - Mitigation: Retry logic, clear failure categorization

### Recommendations for Enterprise Scale

1. **Invest in contract testing early**: Prevents integration issues
2. **Automate baseline updates**: Manual baselines become stale
3. **Monitor test metrics over time**: Catch gradual degradation
4. **Separate adversarial tests**: Don't block releases on edge cases
5. **Use feature flags**: Enable gradual rollout of classification changes

---

## 10. Quick Reference Commands

```bash
# Unit tests (fast, no external deps)
pytest -m unit -v

# Integration tests (requires sandbox)
pytest -m integration -v --sandbox-url=$SANDBOX_URL

# Quality tests (logs to MLFlow)
MLFLOW_TRACKING_URI=$URI pytest -m quality

# Contract verification
pact-verifier --provider-base-url=$PROVIDER_URL --pact-url=./pacts/

# Performance tests (requires JMeter)
jmeter -n -t performance_tests.jmx -l results.jtl

# Regression check
python scripts/check_regression.py --current=results.json --baseline=baseline.json

# Generate test report
pytest --html=report.html --self-contained-html
```

---

## References

- Official AIAI Testing Documentation: `docs/Automation Testing/AIAI_automation_testing.txt`
- Pact IO Documentation: https://docs.pact.io/
- MLFlow Documentation: https://mlflow.org/docs/latest/
- LangGraph Tracing: https://langchain-ai.github.io/langgraph/

---

**Document Version**: 1.0.0
**Last Updated**: February 6, 2026
