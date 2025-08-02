import queue
import random
import threading
from dataclasses import dataclass
from uuid import UUID

import requests


@dataclass
class Settings:
    url: str = "http://localhost:8000/metrics/v1/metric"
    test_films: tuple[UUID] = (
        UUID("3e5351d6-4e4a-486b-8529-977672177a07"),
        UUID("a88cbbeb-b998-4ca6-aeff-501463dcdaa0"),
        UUID("7f28af8a-c629-4af0-b87b-39368a5b8464"),
        UUID("ee1baa06-a221-4d8c-8678-992e8e84c5c1"),
        UUID("e5a21648-59b1-4672-ac3b-867bcd64b6ea"),
        UUID("f061235e-779f-4a59-9eaa-fc533c3c0584"),
        UUID("b16d59f7-a386-467b-bea3-35e7ffbba902"),
        UUID("53d660a1-be2b-4b53-9761-0a315a693789"),
        UUID("0312ed51-8833-413f-bff5-0e139c11264a"),
        UUID("991d143e-1342-4f7c-abf0-a9ede3abba20"),
        UUID("248041f8-8c65-4539-b684-e8f4cd01d10f"),
        UUID("db594b91-a587-48c4-bac9-5c6be5e4cf33"),
        UUID("f553752e-71c7-4ea0-b780-41408516d0f4"),
        UUID("00e2e781-7af9-4f82-b4e9-14a488a3e184"),
        UUID("aa5aea7a-cd65-4aec-963f-98375b370717"),
    )
    max_workers: int = 5
    request_timeout: int = 10


class RequestWorker:

    def __init__(self, config: Settings):
        self.semaphore = threading.Semaphore(config.max_workers)
        self.lock = threading.Lock()
        self.task_queue = queue.Queue()
        self.results = []
        self.request_timeout = config.request_timeout
        self.workers = []

    def create_task(self, url: str, payload: dict | None = None) -> None:
        self.task_queue.put((url, payload))

    @staticmethod
    def _send_request_post(url: str, payload: dict | None = None) -> None:
        requests.post(url, json=payload)

    def _worker(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                self.task_queue.task_done()
                break

            url, payload = task
            with self.semaphore:
                result = self._send_request_post(url, payload)

                with self.lock:
                    self.results.append(result)

            self.task_queue.task_done()

    def start(self, num_workers=10):
        self.workers = [threading.Thread(target=self._worker) for _ in range(num_workers)]

        for worker in self.workers:
            worker.daemon = True
            worker.start()

    def stop(self):
        for _ in self.workers:
            self.task_queue.put(None)

        for worker in self.workers:
            worker.join(timeout=5.0)

    def wait_completion(self):
        self.task_queue.join()
        self.stop()
        return self.results


def main():
    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    config = Settings()
    worker = RequestWorker(config)

    worker.start()

    for _ in range(1000):
        worker.create_task(
            config.url,
            {
                "event_params": {
                    "rating": random.choice(["4", "9", "10"]),
                    "watch_position": "00:45:30",
                },
                "event_type": random.choice(["like", "watch_progress"]),
                "film_uuid": str(random.choice(config.test_films)),
                "message_event": "Событие от кого-то",
                "user_timestamp": "2023-01-01T00:00:00Z",
            },
        )
    worker.wait_completion()
    logger.info("БД успещно наполнена")


if __name__ == "__main__":
    main()
