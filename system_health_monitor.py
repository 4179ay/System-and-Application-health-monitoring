#!/usr/bin/env python3

"""
System Health Monitoring Script

Monitors:
- CPU usage
- Memory usage
- Disk usage
- Number of running processes

Alerts are printed to the console and written to a log file when
configured thresholds are exceeded.
"""

import argparse
import logging
import platform
import socket
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    print("Error: psutil is not installed.")
    print("Install dependencies with: pip install -r requirements.txt")
    sys.exit(1)


DEFAULT_CPU_THRESHOLD = 80.0
DEFAULT_MEMORY_THRESHOLD = 80.0
DEFAULT_DISK_THRESHOLD = 80.0
DEFAULT_PROCESS_THRESHOLD = 200
DEFAULT_INTERVAL = 60
DEFAULT_LOG_FILE = "system_health.log"


def configure_logging(log_file: str) -> None:
    """Configure logging to both a file and the console."""
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def check_cpu(threshold: float) -> tuple[float, bool]:
    """Return CPU usage and whether it exceeds the threshold."""
    usage = psutil.cpu_percent(interval=1)
    return usage, usage > threshold


def check_memory(threshold: float) -> tuple[float, bool]:
    """Return memory usage and whether it exceeds the threshold."""
    usage = psutil.virtual_memory().percent
    return usage, usage > threshold


def check_disk(path: str, threshold: float) -> tuple[float, bool]:
    """Return disk usage and whether it exceeds the threshold."""
    usage = psutil.disk_usage(path).percent
    return usage, usage > threshold


def check_processes(threshold: int) -> tuple[int, bool]:
    """Return running process count and whether it exceeds the threshold."""
    process_count = len(psutil.pids())
    return process_count, process_count > threshold


def run_health_check(args: argparse.Namespace) -> bool:
    """Run one complete system health check."""
    logging.info("Starting system health check")

    cpu, cpu_alert = check_cpu(args.cpu_threshold)
    memory, memory_alert = check_memory(args.memory_threshold)
    disk, disk_alert = check_disk(args.disk_path, args.disk_threshold)
    processes, process_alert = check_processes(args.process_threshold)

    print("\n===== SYSTEM HEALTH REPORT =====")
    print(f"Hostname          : {socket.gethostname()}")
    print(f"Operating System  : {platform.system()} {platform.release()}")
    print(f"CPU Usage         : {cpu:.1f}%")
    print(f"Memory Usage      : {memory:.1f}%")
    print(f"Disk Usage ({args.disk_path}) : {disk:.1f}%")
    print(f"Running Processes : {processes}")
    print("================================")

    alerts = []

    if cpu_alert:
        alerts.append(
            f"CPU usage exceeded threshold: {cpu:.1f}% > {args.cpu_threshold:.1f}%"
        )

    if memory_alert:
        alerts.append(
            f"Memory usage exceeded threshold: "
            f"{memory:.1f}% > {args.memory_threshold:.1f}%"
        )

    if disk_alert:
        alerts.append(
            f"Disk usage exceeded threshold: "
            f"{disk:.1f}% > {args.disk_threshold:.1f}%"
        )

    if process_alert:
        alerts.append(
            f"Running processes exceeded threshold: "
            f"{processes} > {args.process_threshold}"
        )

    if alerts:
        print("\n⚠ ALERTS")
        for alert in alerts:
            print(f"  - {alert}")
            logging.warning(alert)
    else:
        print("\n✓ System health is within configured thresholds.")
        logging.info("System health is within configured thresholds.")

    logging.info("Health check completed")
    return bool(alerts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor Linux system health and generate threshold alerts."
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Seconds between checks in continuous mode (default: {DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "--cpu-threshold",
        type=float,
        default=DEFAULT_CPU_THRESHOLD,
        help=f"CPU alert threshold percentage (default: {DEFAULT_CPU_THRESHOLD})",
    )
    parser.add_argument(
        "--memory-threshold",
        type=float,
        default=DEFAULT_MEMORY_THRESHOLD,
        help=f"Memory alert threshold percentage (default: {DEFAULT_MEMORY_THRESHOLD})",
    )
    parser.add_argument(
        "--disk-threshold",
        type=float,
        default=DEFAULT_DISK_THRESHOLD,
        help=f"Disk alert threshold percentage (default: {DEFAULT_DISK_THRESHOLD})",
    )
    parser.add_argument(
        "--process-threshold",
        type=int,
        default=DEFAULT_PROCESS_THRESHOLD,
        help=f"Running process alert threshold (default: {DEFAULT_PROCESS_THRESHOLD})",
    )
    parser.add_argument(
        "--disk-path",
        default="/",
        help="Filesystem path to monitor (default: /)",
    )
    parser.add_argument(
        "--log-file",
        default=DEFAULT_LOG_FILE,
        help=f"Log file path (default: {DEFAULT_LOG_FILE})",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one health check and exit",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.interval <= 0:
        raise ValueError("Interval must be greater than 0.")
    if not 0 <= args.cpu_threshold <= 100:
        raise ValueError("CPU threshold must be between 0 and 100.")
    if not 0 <= args.memory_threshold <= 100:
        raise ValueError("Memory threshold must be between 0 and 100.")
    if not 0 <= args.disk_threshold <= 100:
        raise ValueError("Disk threshold must be between 0 and 100.")
    if args.process_threshold < 0:
        raise ValueError("Process threshold cannot be negative.")
    if not Path(args.disk_path).exists():
        raise ValueError(f"Disk path does not exist: {args.disk_path}")


def main() -> None:
    args = parse_args()

    try:
        validate_args(args)
        configure_logging(args.log_file)
    except (ValueError, OSError) as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)

    logging.info("System Health Monitor started")

    if args.once:
        run_health_check(args)
        return

    print("System Health Monitor is running.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            run_health_check(args)
            print(f"\nNext check in {args.interval} seconds...")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        logging.info("System Health Monitor stopped by user.")


if __name__ == "__main__":
    main()
