import time
import logging
from functools import wraps
from typing import Type, Tuple

logger = logging.getLogger(__name__)

def retry_on_exception(
    exceptions: Tuple[Type[Exception], ...],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _delay = delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Échec après {max_retries} tentatives : {e}")
                        raise
                    logger.warning(
                        f"Tentative {attempt+1}/{max_retries} échouée : {e}. "
                        f"Nouvel essai dans {_delay:.1f}s"
                    )
                    time.sleep(_delay)
                    _delay *= backoff
            return None
        return wrapper
    return decorator