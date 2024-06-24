from functools import wraps


def forbid_offline(func):
    """
    Custom decorator to forbid method interact with remote service in offline mode.
    Returns:
    """

    # uses functools.wraps to preserve the original function's metadata.
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.client.offline:
            raise ValueError("Service is not available in offline mode.")
        return func(self, *args, **kwargs)

    # important! Custom decorator needs to preserve the original function's docstring
    wrapper.__doc__ = func.__doc__

    return wrapper
