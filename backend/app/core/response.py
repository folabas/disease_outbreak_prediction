from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse
from datetime import datetime, timezone


def success(data: Any, message: Optional[str] = None, status_code: int = 200) -> JSONResponse:
    """Return a normalized success envelope.

    Structure: {"status": "success", "data": {...}, "message"?, "timestamp": ISO8601}
    """
    body: Dict[str, Any] = {
        "status": "success",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if message:
        body["message"] = message
    return JSONResponse(status_code=status_code, content=body)