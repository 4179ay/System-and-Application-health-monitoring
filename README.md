# Python Monitoring Tasks - Submission

This project contains both monitoring tasks from the technical assessment.

## Project Structure

```text
system-health-monitor-submission/
├── system_health_monitor.py
├── application_health_checker.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Task 1 - System Health Monitor

`system_health_monitor.py` monitors four Linux system metrics:

- CPU utilization
- Memory utilization
- Disk utilization
- Number of running processes

The script compares each metric with a configurable threshold. When a threshold is exceeded, it prints an alert and writes the event to `system_health.log`.

### Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run once

```bash
python system_health_monitor.py --once
```

### Run continuously

```bash
python system_health_monitor.py
```

The default monitoring interval is 60 seconds. Stop continuous monitoring with `Ctrl+C`.

### Customize thresholds

```bash
python system_health_monitor.py \
    --cpu-threshold 70 \
    --memory-threshold 75 \
    --disk-threshold 85 \
    --process-threshold 250 \
    --interval 30
```

### Default thresholds

| Metric | Default |
|---|---:|
| CPU usage | 80% |
| Memory usage | 80% |
| Disk usage | 80% |
| Running processes | 200 |
| Monitoring interval | 60 seconds |

## Task 2 - Application Health Checker

`application_health_checker.py` checks whether a web application is reachable and functioning correctly by making an HTTP request and evaluating the HTTP status code.

### Status rules

- HTTP `2xx` response: **UP**
- HTTP `3xx` response: **DOWN** for this task because the requested endpoint did not directly return a successful response
- HTTP `4xx` or `5xx` response: **DOWN**
- Timeout: **DOWN**
- Connection/DNS error: **DOWN**

The checker reports the URL, HTTP status code, response time, and final status. Failed checks are retried by default and results are written to `application_health.log`.

### Run the application checker

```bash
python application_health_checker.py https://example.com
```

### Custom timeout and retries

```bash
python application_health_checker.py https://example.com --timeout 5 --retries 3
```

### Exit codes

- `0` = application is UP
- `1` = application is DOWN or configuration failed

This makes the script suitable for use in shell scripts and CI/CD pipelines.

## Testing Examples

### Test a working endpoint

```bash
python application_health_checker.py https://example.com
```

Expected result: an HTTP 2xx response and `Status: UP`.

### Test an unavailable endpoint

```bash
python application_health_checker.py https://example.com/this-page-does-not-exist
```

Expected result: an HTTP error such as `404` and `Status: DOWN`.

### Task 1 quick test

```bash
python system_health_monitor.py --once
```

The output should display CPU, memory, disk, and running-process information.

## Dependencies

Task 1 uses `psutil`. Task 2 uses Python's standard-library `urllib`, so no additional third-party HTTP library is required.

Install all project dependencies with:

```bash
pip install -r requirements.txt
```

