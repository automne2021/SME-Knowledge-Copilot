"""Safe typed worker errors: never retain raw document/model/SQL exception strings."""


class WorkerError(Exception):
    def __init__(self, code: str, retryable: bool = False):
        self.code, self.retryable = code, retryable
        super().__init__(code)


class LeaseLost(WorkerError):
    def __init__(self):
        super().__init__("lease_lost")
