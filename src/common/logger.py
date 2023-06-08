import logging

formatter = "[%(levelname)-8s] %(asctime)s %(name)-12s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)

logger = logging.getLogger(__name__)
