import logging

from readers.base_embedding import get_default_embedding_model
from config.settings import EMBEDDING_PRE_LOAD

logger = logging.getLogger(__name__)

# implicitly init default model

if EMBEDDING_PRE_LOAD:
    get_default_embedding_model()
    logger.info("successfully init default embedding model")
