# # obs/__init__.py
# """
# Observability bootstrap: JSON logging + Prometheus metrics + /healthz endpoint
# Drop this folder in your repo and import obs.init() before anything else.
# """

# import logging
# import sys
# from prometheus_client import Counter, Histogram, start_http_server
# import structlog

# # ── 1. Structured logging  ────────────────────────────────────────────────
# def _configure_logging():
#     structlog.configure(
#         processors=[
#             structlog.processors.TimeStamper(fmt="iso"),
#             structlog.processors.add_log_level,
#             structlog.processors.StackInfoRenderer(),
#             structlog.processors.format_exc_info,
#             structlog.processors.JSONRenderer(),
#         ],
#         wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
#         logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
#     )

# # expose a logger shortcut
# log = structlog.get_logger()

# # ── 2. Prometheus metrics  ────────────────────────────────────────────────
# CALLS          = Counter("calls_total",          "Total voice calls handled")
# BOOKINGS       = Counter("bookings_total",       "Appointments booked")
# WA_SENT        = Counter("whatsapp_sent_total",  "WhatsApp confirmations sent")
# ERRORS         = Counter("errors_total",         "Unhandled exceptions")
# LLM_LATENCY    = Histogram("llm_latency_seconds","LLM response latency")

# def _start_metrics_server(port: int = 9102):
#     # forks a lightweight HTTP thread inside the agent container
#     start_http_server(port)
#     log.info("prometheus_server_started", port=port)

# # ── 3. Public init() to call from main  ───────────────────────────────────
# def init():
#     _configure_logging()
#     _start_metrics_server()
#     log.info("observability_bootstrap_complete")


### --- obs/__init__.py ---
"""
obs – tiny observability helper
• JSON logs (structlog)
• Prometheus metrics (/metrics on port 9102)
Call `obs.init()` *once* at the very top of agent.py
"""

import sys
import structlog
from prometheus_client import Counter, Histogram, start_http_server
import logging

# ───────────────────── logging ────────────────────

def _setup_logging():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )

log = structlog.get_logger()

# ───────────────────── metrics ────────────────────
CALLS       = Counter("calls_total",          "Total voice calls handled")
BOOKINGS    = Counter("bookings_total",       "Appointments booked")
WA_SENT     = Counter("whatsapp_sent_total",  "WhatsApp confirmations sent")
ERRORS      = Counter("errors_total",         "Unhandled exceptions")
LLM_LATENCY = Histogram("llm_latency_seconds","LLM response latency")

def _start_metrics_server(port: int = 9102):
    start_http_server(port)
    log.info("prometheus_server_started", port=port)

# ───────────────────── public bootstrap ────────────────────

def init():
    _setup_logging()
    _start_metrics_server()
    log.info("observability_bootstrap_complete")
