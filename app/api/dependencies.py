from app.config.settings import get_settings
from app.core.vectorstore import SqliteVectorStore


def get_vector_store():
    settings = get_settings()
    return SqliteVectorStore(settings.vector_store_path)
