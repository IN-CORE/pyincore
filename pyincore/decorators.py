def forbid_offline(func):
    """
    Custom decorator to forbid method interact with remote service in offline mode.
    Returns:
    """
    def wrapper(self, *args, **kwargs):
        if self.client.offline:
            raise ValueError("Service is not available in offline mode.")
        return func(self, *args, **kwargs)

    return wrapper
