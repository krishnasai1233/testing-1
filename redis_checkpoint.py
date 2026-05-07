import os
import redis
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

import builtins

_original_print = builtins.print
def print(*args, **kwargs):
    message = " ".join(str(a) for a in args)
    logger.info(message)
    _original_print(*args, **kwargs)

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PWD = os.getenv('REDIS_PWD')

# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    password=REDIS_PWD,
    ssl=True,
    db=0,
    decode_responses=True
)

# # -----------------------------
# # LangGraph checkpoint (unchanged)
# # -----------------------------
# redis_checkpoint_saver = RedisSaver(redis_client=redis_client)
# redis_checkpoint_saver.setup()
# logger.info(f"Redis Setup is done: {REDIS_HOST}")

# # -----------------------------
# # YOUR PAYLOAD QUEUE LOGIC
# # -----------------------------

QUEUE_NAME = "gitlab:webhook_queue"


def enqueue_payload(payload: dict):
    """
    Save incoming webhook payload into Redis queue
    """
    redis_client.lpush(QUEUE_NAME, json.dumps(payload))
    queue_size = redis_client.llen(QUEUE_NAME)
    logger.info(f"Payload queued | queue={QUEUE_NAME} | size={queue_size}")


def get_next_payload():
    logger.info(f"Waiting for payload | queue={QUEUE_NAME}")
    result = redis_client.brpop(QUEUE_NAME, timeout=5)  # timeout avoids infinite block
    if result is None:
        return None
    _, payload = result
    logger.info(f"Payload popped | queue={QUEUE_NAME}")
    return json.loads(payload)

def ack_payload(payload: dict):
    # call this in _process() after graph.invoke() succeeds
    redis_client.lrem(PROCESSING_KEY, 1, json.dumps(payload))
