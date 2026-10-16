from functools import wraps
from inspect import signature
import json
import logging
from time import perf_counter, thread_time

import psutil


logger = logging.getLogger('uvicorn.error')


def logged_tool(function):
    """Measure dispatched synchronous tools in their execution thread."""
    function_signature = signature(function)

    @wraps(function)
    def wrapper(*args, **kwargs):
        arguments = function_signature.bind(*args, **kwargs)
        arguments.apply_defaults()
        process = psutil.Process()
        record = {
            'tool': function.__name__,
            'parameters': dict(arguments.arguments),
            'input_payload_bytes': len(json.dumps(
                dict(arguments.arguments), ensure_ascii=False,
                separators=(',', ':')).encode('utf-8')),
            'output_payload_bytes': None,
            'status': 'success',
            'rss_before_bytes': process.memory_info().rss,
        }
        started = perf_counter()
        cpu_started = thread_time()
        try:
            result = function(*args, **kwargs)
            # Tools return Pydantic models; count their compact JSON payload.
            record['output_payload_bytes'] = len(result.model_dump_json().encode('utf-8'))
            return result
        except BaseException as error:
            record.update(status='error', error_type=type(error).__name__)
            raise
        finally:
            record.update(
                elapsed_ms=(perf_counter() - started) * 1000,
                cpu_ms=(thread_time() - cpu_started) * 1000,
                rss_after_bytes=process.memory_info().rss,
            )
            logger.info(json.dumps(record))

    return wrapper
