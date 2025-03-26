class ConnectionManager:
    def __init__(self, call=None):
        self.call = call

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Stub implementation - no cleanup needed yet
        pass
