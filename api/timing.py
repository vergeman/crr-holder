from functools import wraps
from inspect import signature
import logging
import os
from time import perf_counter


ENABLED_TIMED = os.environ.get("ENABLED_TIMED") == "1"

# Logger name is uvicorn.error; logger.info sets severity.
logger = logging.getLogger("uvicorn.error")


def timed(function):
    """Use @timed on synchronous services; ENABLED_TIMED=1 enables INFO logs."""
    if not ENABLED_TIMED:
        return function

    # Inspect parameter names, order, and defaults once when decorating.
    function_signature = signature(function)

    @wraps(function)
    def wrapper(*args, **kwargs):
        """Call the original service and log its inputs and elapsed time.

        The captured signature binds positional and keyword inputs to parameter
        names; apply_defaults fills in omitted optional arguments.

        function(*args, **kwargs) invokes the original service with the caller's
        arguments and returns its result.

        @wraps preserves the service's name, docstring, and other metadata.
        """
        # Capture named inputs and defaults before the service can modify them.
        # exclude 'db' for now since its a noisy common obj
        arguments = function_signature.bind(*args, **kwargs)
        arguments.apply_defaults()
        parameters = repr({
            name: value for name, value in arguments.arguments.items()
            if name != "db"
        })

        started = perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            # Log successful and failed calls, excluding capture and logging time.
            elapsed_ms = (perf_counter() - started) * 1000
            logger.info("%s parameters=%s elapsed_ms=%.2f",
                        function.__name__, parameters, elapsed_ms)

    return wrapper
