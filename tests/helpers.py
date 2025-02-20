import random
import string
import uuid


def next_random_string(charset=string.ascii_letters, length: int = 20):
    assert length > 0
    assert len(charset) > 0

    return "".join([random.choice(charset) for _ in range(length)])


def next_uuid():
    return str(uuid.uuid4())
