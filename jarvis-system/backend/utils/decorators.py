import time
import functools
from typing import Callable, Any, Type
from utils.logger import logger

class CustomAPIError(Exception):
    """Base class for custom API exceptions."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def timing_decorator(func: Callable) -> Callable:
    """Monitors and logs the execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        logger.debug(f"Function '{func.__name__}' executed in {elapsed:.4f} seconds.")
        return result
    return wrapper

def retry_decorator(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0, exceptions=(Exception,)) -> Callable:
    """Retries a function upon failure with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Function '{func.__name__}' failed after {max_retries} attempts. Error: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed for '{func.__name__}'. Retrying in {delay}s. Error: {e}")
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

def singleton(cls: Type) -> Type:
    """Decorator to make a class a Singleton."""
    instances = {}

    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

def memoization_decorator(func: Callable) -> Callable:
    """Caches the results of expensive function calls based on arguments."""
    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # We need a hashable key. Dicts/lists in kwargs break this, so we use string representation as fallback for unhashables.
        try:
            key = (args, frozenset(kwargs.items()))
        except TypeError:
            key = str((args, kwargs))
            
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        else:
            logger.debug(f"Cache hit for function '{func.__name__}'")
        return cache[key]
        
    wrapper.cache_clear = lambda: cache.clear()
    return wrapper

def error_handler(func: Callable) -> Callable:
    """Catches exceptions and wraps them in custom API errors for consistent handling."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CustomAPIError:
            # Re-raise custom errors as they are already handled
            raise
        except ValueError as e:
            logger.error(f"Validation error in '{func.__name__}': {str(e)}")
            raise CustomAPIError(str(e), status_code=400)
        except Exception as e:
            logger.error(f"Unexpected error in '{func.__name__}': {str(e)}", exc_info=True)
            raise CustomAPIError(f"An unexpected internal error occurred.", status_code=500)
    return wrapper
