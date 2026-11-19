# Overdrive

**An AI-assisted process-analysis API for investigating operational bottlenecks.**

Overdrive accepts a process description and optional structured data, sends that bounded input to a configured language-model provider, and returns a validated, ranked set of candidate bottlenecks with root-cause hypotheses and proposed fixes.

**Current stage:** an early API MVP. Overdrive does not yet connect to live operational systems, independently verify its hypotheses, or execute process changes.

## Why these features were chosen

Overdrive is designed as a controlled analysis pipeline rather than an autonomous agent with unrestricted access to business systems.

| Feature | Why we chose it | Trade-off / boundary |
|---|---|---|
| FastAPI service boundary | Gives the analysis engine a clear HTTP contract and makes it straightforward to integrate with dashboards, scripts and future clients. | The current MVP exposes a small API, not a complete operations platform or user-facing dashboard. |
| Provider abstraction | A common complete() interface allows the application to switch between supported model providers without rewriting the analysis endpoint. | Provider SDKs, credentials, model behavior, latency and cost still differ. A common interface does not make outputs equivalent. |
| Remote and local provider adapters | Supports hosted models as well as a local Ollama endpoint, giving development and deployment more flexibility. | Local inference depends on the user's machine, installed model and Ollama service. Remote providers require valid credentials and network access. |
| Structured request validation | Rejects malformed process descriptions and unexpected request fields before they reach the model. | Valid input structure does not mean the process description itself is complete or factually correct. |
| Bounded process data | Limits serialized data to 16 KiB, nesting to 8 levels and traversal to 2,000 values. This reduces accidental oversized or pathological payloads. | These are defensive request limits, not a substitute for authentication, rate limiting or infrastructure-level abuse protection. |
| Prompt/data separation | Serializes the user's process description and data as a JSON payload and explicitly treats them as untrusted data. This helps resist instruction-like text embedded in business data. | Prompt-injection defenses are layered mitigations, not a guarantee that a model will always follow the intended instructions. |
| Strict response schema | Pydantic validates required fields, severity values, confidence bounds, text lengths and a contiguous 1-to-7 rank sequence. | Schema-valid JSON can still contain incorrect analysis. Structural validity is not factual verification. |
| Ranked bottlenecks | Gives teams a prioritised shortlist rather than an unstructured block of model-generated prose. | The ranking is the model's judgement based on supplied context; it is not a measured operational ranking. |
| Explicit uncertainty and ROI handling | The prompt asks the model to distinguish observations from hypotheses and use Requires measurement when evidence cannot support an ROI estimate. | The API does not calculate savings or validate ROI against real operational data. |
| Safe API errors | Returns generic provider-configuration and upstream-failure messages to clients while retaining diagnostic details in server logs. | Operators still need secure log handling, monitoring and deployment-level observability. |
| Health endpoint | Lets a deployment check whether the API process is responding and see the selected provider. | It does not perform a live upstream model request and therefore does not prove provider availability. |

## How it works

~~~text
Process description + optional structured data
                    |
                    v
         Request and size validation
                    |
                    v
        JSON-encoded untrusted payload
                    |
                    v
        Configured LLM provider adapter
                    |
                    v
          Model-generated JSON text
                    |
                    v
        JSON parsing + Pydantic schema
                    |
                    v
       Ranked candidate bottleneck report
~~~

The system asks the model to separate evidence in the supplied input from hypotheses that need investigation. It must not invent measurements, benchmarks, savings or ROI. When the supplied evidence is insufficient, the requested ROI value is Requires measurement.

## Current capabilities

- FastAPI health and process-analysis endpoints.
- Provider selection through environment configuration.
- Provider adapters for Anthropic, OpenAI, Google Gemini, Groq and Ollama.
- Request validation and bounded JSON input.
- Prompt/data separation for user-supplied process text and data.
- Strict schema validation for model-generated bottleneck reports.
- Three to seven ranked bottlenecks, each with severity, root-cause hypothesis, proposed fix, ROI text and confidence.
- Generic client-facing errors for provider configuration and upstream request failures.

Provider availability depends on the selected adapter, installed SDK, credentials, model access and (for Ollama) a reachable local service.

## Requirements

- Python 3.11+
- A configured provider and its credentials, or a running Ollama service with a compatible local model
- Network access for remote providers

## Setup

~~~bash
git clone https://github.com/Gitcoder12/Overdrive.git
cd Overdrive
python -m venv .venv
~~~

Activate the environment:

~~~bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
~~~

Install the package and development dependencies:

~~~bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
~~~

Create the local environment file:

~~~bash
# macOS / Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
~~~

Edit .env and configure LLM_PROVIDER, the matching API key (if required), and optionally LLM_MODEL. Never commit real credentials.

## Configuration

| Variable | Purpose |
|---|---|
| LLM_PROVIDER | anthropic, openai, google, groq or ollama |
| LLM_MODEL | Optional model identifier; an adapter default is used when empty |
| MAX_TOKENS | Maximum completion token budget (100–8,000) |
| TEMPERATURE | Configurable sampling setting |
| ANTHROPIC_API_KEY | Anthropic credential |
| OPENAI_API_KEY | OpenAI credential |
| GOOGLE_API_KEY | Google credential |
| GROQ_API_KEY | Groq credential |
| OLLAMA_BASE_URL | Local Ollama service URL |
| DEBUG | Debug setting |

Only the API key for the selected remote provider is required. Ollama does not require a provider API key. The default model is adapter-specific; setting LLM_MODEL overrides it.

## Run the API

~~~bash
uvicorn app.main:app --reload
~~~

The local service is available at http://127.0.0.1:8000.

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

## API

### Health check

~~~bash
curl http://127.0.0.1:8000/health
~~~

Returns the API process status and configured provider name. It does **not** make a test call to the upstream model provider.

### Analyze a process

~~~bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "process": "Describe how incoming customer support requests are assigned and resolved.",
    "data": {
      "daily_requests": 500,
      "agents": 12,
      "average_resolution_hours": 18
    }
  }'
~~~

Request constraints:

- process: 10–5,000 characters, with at least 10 non-whitespace characters.
- data: optional JSON object, limited to 16 KiB after serialization, 8 nesting levels and 2,000 values.
- Unknown top-level request fields are rejected.

A successful response contains:

- provider: selected provider/model label.
- summary: concise overview.
- bottlenecks: 3–7 ranked entries. Each includes rank, name, severity, root_cause, fix, roi_estimate and confidence.

Ranks must be unique, ascending and contiguous from 1. Severity is high, medium or low; confidence must be between 0.0 and 1.0.

## Interpreting the result responsibly

Overdrive produces **candidate explanations**, not established root causes.

1. Check which statements are directly supported by the supplied process data.
2. Treat root-cause descriptions and fixes as hypotheses.
3. Collect operational measurements before accepting a proposed intervention.
4. Establish a baseline and compare outcomes after a controlled change.
5. Do not treat model confidence as a statistically calibrated probability.
6. Do not treat roi_estimate as a financial forecast. If evidence is missing, measure before estimating.

The API validates the response structure; it cannot guarantee that a model-generated explanation, confidence value, priority or recommendation is correct.

## Tests and development

Run the test suite:

~~~bash
pytest
~~~

The current tests cover API validation, response-schema rejection, provider failures, bounded input and prompt/data separation. They use mocked model responses; they do not benchmark real provider quality or prove real-world bottleneck accuracy.

Optional quality checks:

~~~bash
ruff check .
mypy app
~~~

## Current limitations and next engineering milestones

Not yet established or implemented:

- Accuracy across representative real-world process benchmarks.
- Measured operational savings, ROI or throughput improvements.
- Live integrations with ERP, CRM, ticketing, warehouse or telemetry systems.
- Autonomous investigation, approvals or execution of process changes.
- Persistent analysis history, user accounts, authentication and role-based access.
- Production rate limiting, quotas, provider retries and comprehensive observability.
- Calibrated confidence estimates and independent evidence verification.
- Robustness across all providers, models and process domains.

These are potential future milestones, not shipped features.

## Development principles

- Prefer evidence-backed claims over model confidence or persuasive prose.
- Treat external process descriptions and data as untrusted input.
- Bound requests and validate model output before returning it.
- Keep provider integration replaceable and the API contract explicit.
- Measure operational outcomes before claiming optimization or ROI.
- Add autonomy only after reliable evaluation, approval and rollback mechanisms exist.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Author

Dharavath Satvik
