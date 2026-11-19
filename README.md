# Overdrive

**An AI-assisted process-analysis API for investigating operational bottlenecks.**

Overdrive accepts a process description and optional structured data, sends the bounded input to a configured language-model provider, and returns a validated, ranked list of candidate bottlenecks with root-cause hypotheses and proposed fixes.

The current repository is an early API MVP. It is not yet a general-purpose autonomous optimization platform, and it does not execute changes in external systems.

## Current capabilities

- FastAPI service with a health endpoint and a process-analysis endpoint
- Configurable LLM provider settings, including remote-provider API-key fields and a local Ollama URL
- Structured request validation and bounded JSON input
- Schema validation for model-generated bottleneck reports
- Ranked bottlenecks with severity, root-cause hypothesis, proposed fix, confidence, and an ROI field
- Safe API error responses that avoid returning raw provider exception details

Model output is advisory. Findings and recommendations should be reviewed by a person and validated against real operational measurements.

## How it works

```text
Process description + optional data
                |
                v
        Request validation
                |
                v
     Configured LLM provider
                |
                v
      Structured JSON response
                |
                v
       Pydantic validation
                |
                v
       Ranked analysis report
```

The API asks the model to distinguish observations supported by the supplied input from hypotheses that need investigation. When the evidence does not support a defensible ROI estimate, the expected value is `Requires measurement`.

## Requirements

- Python 3.11+
- A configured provider and its credentials, or a running local model service if using a compatible local-provider configuration

## Setup

Clone the repository and install it with its development dependencies:

```bash
git clone https://github.com/Gitcoder12/Overdrive.git
cd Overdrive
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\\Scripts\\Activate.ps1
```

Install the package:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Create your local environment file:

```bash
# macOS / Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Edit `.env` and configure the provider and matching API key. Never commit real credentials.

## Run the API

```bash
uvicorn app.main:app --reload
```

The local service uses the default Uvicorn address, `http://127.0.0.1:8000`.

Interactive API documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## API

### Health check

```bash
curl http://127.0.0.1:8000/health
```

Returns service status and the configured provider name. It does not establish that an upstream provider request will succeed.

### Analyze a process

```bash
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
```

The `process` field must contain at least 10 non-whitespace characters. Optional `data` must be JSON-compatible and is bounded by size, nesting-depth, and node-count limits.

A successful response contains:

- `provider`: configured provider name
- `summary`: concise analysis overview
- `bottlenecks`: 3–7 ranked items, each with `rank`, `name`, `severity`, `root_cause`, `fix`, `roi_estimate`, and `confidence`

The API validates the response structure; it cannot guarantee that model-generated explanations, confidence values, or recommendations are factually correct.

## Configuration

Configuration is loaded from environment variables (see [.env.example](.env.example)).

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | Provider selection |
| `LLM_MODEL` | Optional model identifier |
| `MAX_TOKENS` | Response token budget |
| `TEMPERATURE` | Sampling temperature |
| `ANTHROPIC_API_KEY` | Anthropic credential |
| `OPENAI_API_KEY` | OpenAI credential |
| `GOOGLE_API_KEY` | Google credential |
| `GROQ_API_KEY` | Groq credential |
| `OLLAMA_BASE_URL` | Local Ollama service URL |
| `DEBUG` | Debug setting |

The checked-in environment template lists `anthropic`, `openai`, `google`, `groq`, and `ollama` as provider choices. Actual availability depends on the provider adapter implementation, credentials, installed SDKs, and upstream service.

## Development

Run the test suite:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

Run static type checking:

```bash
mypy app
```

These are the configured development tools; run them on your current checkout and review the results before treating the build as verified.

## Current status

**Early API MVP — active development.**

The implemented scope is process-description analysis through a configured LLM provider. The broader vision—field intelligence, autonomous investigation, optimization, execution, and continuous learning—is a long-term direction, not a claim about shipped functionality.

### Not yet established

- Reliable bottleneck detection across a representative real-world benchmark
- Measured cost savings, ROI, or operational improvements
- Autonomous execution or integration with live production systems
- Robustness and quality across all providers, models, and process domains
- Production readiness under load

## Development principles

- Ground claims in code, tests, and measured results.
- Treat model-generated conclusions as hypotheses until validated.
- Keep input limits, output validation, and safe error handling.
- Prefer reproducible experiments over unsupported performance claims.
- Add capabilities incrementally and document what is actually implemented.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Author

Dharavath Satvik


---

## Comparison with Existing Open-Source Projects

Overdrive is documented as an LLM-assisted process-analysis API that accepts a process description and optional structured data, then returns ranked bottleneck hypotheses and candidate fixes. The README explicitly describes an early API MVP whose output is advisory and does not execute changes in external systems. These projects provide adjacent process-mining and optimization references.

| Project | Established focus | Relationship to Overdrive |
|---|---|---|
| [PM4Py](https://github.com/pm4py/pm4py-core) | Process mining from event logs, including discovery, conformance and performance analysis | A mature data-driven process-mining library; Overdrive currently accepts user-described processes and bounded input rather than requiring a formal event log. |
| [Google OR-Tools](https://github.com/google/or-tools) | Constraint programming and combinatorial optimization | A mature optimization toolkit; Overdrive proposes candidate fixes through an LLM and does not currently solve or execute an optimization model. |
| [bpmn-js](https://github.com/bpmn-io/bpmn-js) | BPMN process-model visualization and editing | A process-modelling interface; Overdrive's intended role is analysis of bottleneck hypotheses rather than authoring process diagrams. |

### Where Overdrive is different
- **Natural-language process intake:** the API can start from a process description with optional structured metrics instead of requiring a fully instrumented event log.
- **Hypothesis generation:** it returns ranked bottleneck candidates, root-cause hypotheses and proposed fixes in a validated response schema.
- **Human-reviewed recommendations:** the service distinguishes observations from hypotheses and does not execute external changes.

### Where established projects are stronger
PM4Py offers formal process-mining algorithms when event logs are available; OR-Tools provides actual optimization solvers; bpmn-js provides a mature process-model editor. Overdrive's LLM output cannot guarantee factual correctness, causal diagnosis or ROI accuracy.

### Evidence and limitations
Evaluate bottleneck ranking against expert-labelled cases and measured operational outcomes. Distinguish input-supported observations from model-generated hypotheses, and keep ROI as “requires measurement” unless a defensible calculation exists. Benchmark latency, cost and recommendation quality across providers. This is a workflow comparison, not an optimization-effectiveness claim.
