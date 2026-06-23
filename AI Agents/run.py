import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn
from src.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
