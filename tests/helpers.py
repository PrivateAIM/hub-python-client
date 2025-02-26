import os
import random
import string
import time
import uuid

import typing as t


def assert_eventually(callback_fn: t.Callable[[], t.Any]):
    max_retries = int(os.getenv("PYTEST_ASYNC_MAX_RETRIES", "5"))
    delay_millis = int(os.getenv("PYTEST_ASYNC_RETRY_DELAY_MILLIS", "500"))
    e = None

    for _ in range(max_retries):
        try:
            callback_fn()
            return  # return if everything went fine
        except AssertionError as exc_info:
            e = exc_info

        time.sleep(delay_millis / 1_000)

    assert False, f"callback failed after {max_retries} retries: {e}"


def next_random_string(charset=string.ascii_letters, length: int = 20):
    assert length > 0
    assert len(charset) > 0

    return "".join([random.choice(charset) for _ in range(length)])


def next_uuid():
    return str(uuid.uuid4())
