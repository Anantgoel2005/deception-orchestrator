"""Long-running local-lab worker. Production control planes do not mount Docker."""
from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.services.log_monitor import monitor_honeypot_logs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


async def main() -> None:
    if not settings.enable_local_decoys:
        logging.getLogger(__name__).info("Local decoys disabled; worker is idle")
        while True:
            await asyncio.sleep(3600)
    await monitor_honeypot_logs()


if __name__ == "__main__":
    asyncio.run(main())
