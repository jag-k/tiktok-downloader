from contextvars import ContextVar

__all__ = (
    "USER_ID",
    "USERNAME",
    "QUERY",
    "DATA_TYPE",
    "CONTEXT_VARS",
)

USER_ID: ContextVar[int] = ContextVar("USER_ID", default=0)
USERNAME: ContextVar[str] = ContextVar("USERNAME", default="")
QUERY: ContextVar[str] = ContextVar("QUERY", default="")
DATA_TYPE: ContextVar[str] = ContextVar("DATA_TYPE", default="")
CONTEXT_VARS: list[ContextVar] = [
    USER_ID,
    USERNAME,
    QUERY,
    DATA_TYPE,
]
