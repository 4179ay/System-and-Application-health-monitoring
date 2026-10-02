#!/usr/bin/env python3
"""Application Health Checker.

Checks whether a web application is reachable and functioning by validating
its HTTP response status code.

HTTP 2xx responses are considered UP. Redirects, 4xx/5xx responses,
timeouts, DNS failures, and connection errors are considered DOWN.
"""

import argparse
import logging
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 2
DEFAULT_LOG_FILE = "application_health.log"


def configure_logging(log_file: str) -> None:
    """Log health-check results to both the console and a file."""
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def check_application(url: str, timeout: int) -> tuple[bool, int | None, str, float]:
    """Check one URL and return status, HTTP code, message, and response time."""
    start = time.perf_counter()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ApplicationHealthChecker/1.0"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.status
            response.read(1)
            elapsed = time.perf_counter() - start
            if 200 <= status_code < 300:
                return True, status_code, "Application is UP", elapsed
            return False, status_code, f"Application is DOWN (HTTP {status_code})", elapsed

    except urllib.error.HTTPError as exc:
        elapsed = time.perf_counter() - start
        return False, exc.code, f"Application is DOWN (HTTP {exc.code})", elapsed
    except urllib.error.URLError as exc:
        elapsed = time.perf_counter() - start
        reason = getattr(exc, "reason", exc)
        return False, None, f"Application is DOWN ({reason})", elapsed
    except TimeoutError:
        elapsed = time.perf_counter() - start
        return False, None, "Application is DOWN (request timed out)", elapsed
    except Exception as exc:  # Keep the checker from crashing on unexpected network errors.
        elapsed = time.perf_counter() - start
        return False, None, f"Application is DOWN ({exc})", elapsed


def run_health_check(url: str, timeout: int, retries: int) -> bool:
    """Run the health check, retrying transient failures when configured."""
    attempts = retries + 1
    for attempt in range(1, attempts + 1):
        is_up, status_code, message, elapsed = check_application(url, timeout)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        status_text = "UP" if is_up else "DOWN"
        code_text = str(status_code) if status_code is not None else "N/A"

        print("\n===== APPLICATION HEALTH REPORT =====")
        print(f"URL               : {url}")
        print(f"Checked At (UTC)  : {timestamp}")
        print(f"HTTP Status Code  : {code_text}")
        print(f"Response Time     : {elapsed:.3f}s")
        print(f"Status            : {status_text}")
        print(f"Message           : {message}")
        print("=====================================")

        if is_up:
            logging.info("%s | HTTP %s | %.3fs | %s", url, code_text, elapsed, message)
            return True

        logging.warning("Attempt %d/%d | %s | HTTP %s | %.3fs | %s", attempt, attempts, url, code_text, elapsed, message)
        if attempt < attempts:
            time.sleep(1)

    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check application availability using HTTP status codes."
    )
    parser.add_argument("url", help="Application URL to check, for example https://example.com")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds (default: 10)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Number of retries after a failed check (default: 2)")
    parser.add_argument("--log-file", default=DEFAULT_LOG_FILE, help=f"Log file path (default: {DEFAULT_LOG_FILE})")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.timeout <= 0:
        print("Configuration error: timeout must be greater than 0.")
        sys.exit(1)
    if args.retries < 0:
        print("Configuration error: retries cannot be negative.")
        sys.exit(1)
    if not args.url.startswith(("http://", "https://")):
        print("Configuration error: URL must start with http:// or https://.")
        sys.exit(1)

    try:
        configure_logging(args.log_file)
    except OSError as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)

    logging.info("Application Health Checker started for %s", args.url)
    is_up = run_health_check(args.url, args.timeout, args.retries)
    logging.info("Application Health Checker completed: %s", "UP" if is_up else "DOWN")
    sys.exit(0 if is_up else 1)


if __name__ == "__main__":
    main()
