# pipewatch

Lightweight CLI tool to monitor and alert on data pipeline health metrics.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install .
```

---

## Usage

```bash
# Monitor a pipeline and check health metrics
pipewatch monitor --config pipeline.yaml

# Run a one-time health check
pipewatch check --pipeline my_pipeline --threshold 0.95

# List active alerts
pipewatch alerts list
```

**Example `pipeline.yaml`:**

```yaml
pipeline:
  name: my_pipeline
  source: postgresql://localhost/mydb
  checks:
    - metric: row_count
      min: 1000
    - metric: null_rate
      max: 0.05
  alert:
    email: ops@example.com
```

Pipewatch will continuously poll your pipeline, evaluate the defined checks, and fire alerts when thresholds are breached.

---

## Features

- Minimal setup with a single config file
- Supports row count, null rate, latency, and custom metric checks
- Pluggable alert backends (email, Slack, PagerDuty)
- Lightweight — no heavy dependencies

---

## License

This project is licensed under the [MIT License](LICENSE).