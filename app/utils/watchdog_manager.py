import logging
import os
import threading
import time
from typing import Any

from watchdog.observers.polling import PollingObserver

from app.database import SessionLocal
from app.models import WatchedFolder
from watchdog_client.scanner import scan_folder
from watchdog_client.watcher import FileWatcher

logger = logging.getLogger(__name__)

RECONCILE_INTERVAL_SECONDS = 2


class WatchdogManager:
    def __init__(self) -> None:
        self._observer: PollingObserver | None = None
        self._thread: threading.Thread | None = None
        self._watches: dict[str, Any] = {}
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._running:
                return

            self._observer = PollingObserver(timeout=1.0)
            self._observer.start()
            self._running = True

            self._thread = threading.Thread(
                target=self._run,
                name="WatchdogManager",
                daemon=True,
            )
            self._thread.start()

        logger.info("Watchdog manager started")

    def _get_watched_paths(self) -> set[str]:
        db = SessionLocal()
        try:
            return {
                folder.folder_path
                for folder in db.query(WatchedFolder).all()
            }
        finally:
            db.close()

    def _sync_watches(self) -> None:
        if self._observer is None:
            return

        desired_paths = self._get_watched_paths()
        active_paths = set(self._watches)

        # Stop watches for folders deleted through the API.
        for folder_path in active_paths - desired_paths:
            watch = self._watches.pop(folder_path)
            self._observer.unschedule(watch)
            logger.info("Stopped watching folder: %s", folder_path)

        # Scan and start watches for newly added folders.
        for folder_path in desired_paths - active_paths:
            if not os.path.isdir(folder_path):
                logger.warning(
                    "Watched folder is unavailable inside the container: %s",
                    folder_path,
                )
                continue

            logger.info("Scanning newly watched folder: %s", folder_path)
            scan_folder(folder_path)

            watch = self._observer.schedule(
                FileWatcher(),
                folder_path,
                recursive=True,
            )
            self._watches[folder_path] = watch
            logger.info("Now watching folder: %s", folder_path)

    def _run(self) -> None:
        try:
            while self._running:
                try:
                    self._sync_watches()
                except Exception:
                    logger.exception("Failed to reconcile watched folders")

                time.sleep(RECONCILE_INTERVAL_SECONDS)
        finally:
            logger.info("Watchdog manager loop stopped")

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return

            self._running = False
            observer = self._observer
            thread = self._thread

        if observer is not None:
            observer.stop()

        if thread is not None:
            thread.join(timeout=10)

        if observer is not None:
            observer.join(timeout=10)

        with self._lock:
            self._watches.clear()
            self._observer = None
            self._thread = None

        logger.info("Watchdog manager stopped")


watchdog_manager = WatchdogManager()