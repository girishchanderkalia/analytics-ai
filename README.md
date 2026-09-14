# AI-enabled Analytics Demonstrator

OPO monitoring demonstrator for conversational trend investigation and wafer-level deep dive. The application combines an application-owned LangGraph workflow and UI with Analytics Foundation model and data-access adapters.

## Architecture

```text
AnalyticsFoundation/
    Model connectivity, workspace/query adapters, capability and session support

ApplicationUI/
    analytics_agents/opo_monitoring_service/
        FastAPI BFF and LangGraph workflow
    opo_monitoring_ui/static/
        Application-owned HTML, JavaScript, CSS, charts, and wafer map
```

The backend serves the frontend assets. There is no separate frontend dev server in this demonstrator.

## Prerequisites

- Windows with PowerShell or Git Bash
- Python 3.12 or compatible Python 3.x
- Azure CLI, if using the configured model gateway and Key Vault
- Access to the configured model deployment and secret

## First-time setup

From the repository root:

### PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Git Bash

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

The command examples below use the project interpreter directly so the selected virtual environment is explicit.

## Model gateway configuration

The model settings are defined in [AnalyticsFoundation/config.py](AnalyticsFoundation/config.py). Settings use the `ASML_AI_` environment-variable prefix:

```text
ASML_AI_BASE_URL
ASML_AI_DEPLOYMENT
ASML_AI_API_VERSION
ASML_AI_TEMPERATURE
ASML_AI_KEY_VAULT_URL
ASML_AI_SECRET_NAME
ASML_AI_SESSION_DB
```

The default configuration points to the configured platform model endpoint and Key Vault secret. Authenticate locally before starting the service when the defaults are used:

```powershell
az login
```

The application uses `DefaultAzureCredential` to retrieve the model gateway secret. Do not put API keys or secrets in source files.

## Run the full application

The repository also includes a self-contained launcher. Run it from Git Bash or
WSL in the repository root:

```bash
./run.sh start
```

If Git Bash does not preserve the executable bit on Windows, use:

```bash
bash run.sh
```

The launcher supports these lifecycle commands:

```bash
./run.sh start    # install dependencies if needed and start in the background
./run.sh status   # show the PID and URL
./run.sh stop     # stop the process started by run.sh
./run.sh restart  # stop and start again
./run.sh run      # run in the foreground; Ctrl+C stops it
```

`run.sh start` creates `.venv` when needed, installs `requirements.txt`, uses port
8000 when available, falls back to port 8010 when necessary, and starts the combined
backend/frontend service. It writes the process ID to `.opo-monitoring.pid` and logs
to `.opo-monitoring.log`. Set `ASML_AI_PORT` to request a specific port:

```bash
ASML_AI_PORT=8010 ./run.sh
```

On Windows Command Prompt, launch Git Bash first and run `./run.sh`; `.sh` files
are not native `cmd.exe` commands.

Start the backend and frontend together from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn ApplicationUI.analytics_agents.opo_monitoring_service.api:app --host 127.0.0.1 --port 8000
```

Or from Git Bash:

```bash
./.venv/Scripts/python.exe -m uvicorn ApplicationUI.analytics_agents.opo_monitoring_service.api:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

If port 8000 is already in use, select another port:

```powershell
.\.venv\Scripts\python.exe -m uvicorn ApplicationUI.analytics_agents.opo_monitoring_service.api:app --host 127.0.0.1 --port 8010
```

Then open `http://127.0.0.1:8010/`.

## Demonstrator workflow

1. The UI loads the OPO KPI trend chart on page load.
2. Enter a request such as `Show me trends and outliers`.
3. The application reads KPI data and calculates P95/P99 absolute KPI values.
4. The model recommends an absolute cutoff using those values.
5. Approve or edit the recommended cutoff in the agent panel.
6. Select or approve an outlier.
7. Approve dataset registration.
8. The application retrieves and interprets wafer-level data.
9. The model produces a structured summary with finding, confidence, evidence, limitations, alternative explanations, and recommended next actions.

The agent interaction, prompt, evidence, and result are in the right panel. Trend and wafer visualizations are in the left panel.

## Useful endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Serve the application UI |
| `GET /trends` | Return raw trend series used by the chart |
| `POST /chat` | Start an investigation |
| `POST /resume` | Resume an investigation after a user decision |
| `GET /threads/{thread_id}` | Reopen persisted workflow state |
| `GET /sessions/{session_id}/events` | Inspect session evidence and timing events |
| `GET /capabilities` | Inspect registered capability metadata |
| `GET /vendor/plotly.js` | Serve the local Plotly bundle |

Example request:

```powershell
$body = @{ message = "Show me trends and outliers" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/chat -ContentType "application/json" -Body $body
```

## Validation

Compile the project packages:

```powershell
.\.venv\Scripts\python.exe -m compileall -q AnalyticsFoundation ApplicationUI tests scripts
```

The repository includes scripts under [scripts](scripts) for smoke, mode, and threshold checks. The project environment must have `pytest` installed to run the pytest test file:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_services_file_source.py -q
```

## Data and integration status

This is a demonstrator. The current local data path uses:

```text
AnalyticsFoundation/mock_data/opo_dataset.json
```

Workspace registration and Query Engine access are currently simulated/local adapters. The API specifications that describe the intended Analytics Foundation services are in:

- [apis/api.yml](apis/api.yml)
- [apis/qe_api.yml](apis/qe_api.yml)

The application-owned workflow and UI are implemented, but production deployment, live Workspace/Query Engine integration, identity integration, and a generic multi-agent runtime remain future work.

## Stopping the service

Press `Ctrl+C` in the terminal running Uvicorn.
