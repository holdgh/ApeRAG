import logging

from readers.base_embedding import get_default_embedding_model

logger = logging.getLogger(__name__)

# implicitly init default model
get_default_embedding_model()
logger.info("successfully init default embedding model")
