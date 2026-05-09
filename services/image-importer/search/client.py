import meilisearch
from config import settings

_client = meilisearch.Client(settings.meili_host, settings.meili_api_key)


def get_index():
    index = _client.index(settings.meili_index)
    return index


def ensure_index():
    _client.create_index(settings.meili_index, {"primaryKey": "id"})
    index = get_index()
    index.update_searchable_attributes([
        "positive_prompts",
        "negative_prompts",
        "model",
        "styles",
        "loras",
        "comment",
        "filename",
        "scheduler",
        "sampler_name",
    ])
    index.update_filterable_attributes(["rating", "bucket", "already_reviewed"])
    index.update_sortable_attributes(["rating", "image_width", "image_height"])
