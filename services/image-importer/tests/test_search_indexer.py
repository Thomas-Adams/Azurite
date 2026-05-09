import pytest
from unittest.mock import MagicMock


def _make_image(sha256="abc123", file_name="test.png", path="/data", width=512, height=768):
    m = MagicMock()
    m.sha256 = sha256
    m.file_name = file_name
    m.path = path
    m.width = width
    m.height = height
    return m


def _make_generation(model_name="model.safetensors", positive_prompt="a cat", negative_prompt="ugly",
                     styles="Style A, Style B", seed=42, steps=20, cfg=7.0, scheduler="euler"):
    m = MagicMock()
    m.model_name = model_name
    m.positive_prompt = positive_prompt
    m.negative_prompt = negative_prompt
    m.styles = styles
    m.seed = seed
    m.steps = steps
    m.cfg = cfg
    m.scheduler = scheduler
    return m


def _make_lora(name="lora_a"):
    m = MagicMock()
    m.name = name
    return m


def _make_review(rating=1, comment="good"):
    m = MagicMock()
    m.rating = rating
    m.comment = comment
    return m


def _make_storage(url="http://localhost:9000/bucket/1.png", bucket="bucket"):
    m = MagicMock()
    m.url = url
    m.bucket = bucket
    return m


class TestBuildDocument:
    def test_id_is_sha256(self):
        from search.indexer import build_document
        doc = build_document(_make_image(sha256="deadbeef"), _make_generation(), [], _make_review(), _make_storage())
        assert doc["id"] == "deadbeef"

    def test_basic_fields(self):
        from search.indexer import build_document
        doc = build_document(
            _make_image(file_name="img.png", path="/root", width=512, height=768),
            _make_generation(model_name="mymodel.safetensors"),
            [],
            _make_review(rating=2, comment="ok"),
            _make_storage(url="http://minio/b/1.png", bucket="b"),
        )
        assert doc["filename"] == "img.png"
        assert doc["path"] == "/root"
        assert doc["image_width"] == 512
        assert doc["image_height"] == 768
        assert doc["model"] == "mymodel.safetensors"
        assert doc["rating"] == 2
        assert doc["comment"] == "ok"
        assert doc["url"] == "http://minio/b/1.png"
        assert doc["bucket"] == "b"

    def test_styles_split_into_list(self):
        from search.indexer import build_document
        doc = build_document(
            _make_image(), _make_generation(styles="Foo, Bar, Baz"), [], _make_review(), _make_storage()
        )
        assert doc["styles"] == ["Foo", "Bar", "Baz"]

    def test_empty_styles_gives_empty_list(self):
        from search.indexer import build_document
        doc = build_document(_make_image(), _make_generation(styles=None), [], _make_review(), _make_storage())
        assert doc["styles"] == []

    def test_loras_extracted_by_name(self):
        from search.indexer import build_document
        loras = [_make_lora("lora_a"), _make_lora("lora_b")]
        doc = build_document(_make_image(), _make_generation(), loras, _make_review(), _make_storage())
        assert doc["loras"] == ["lora_a", "lora_b"]

    def test_none_named_loras_excluded(self):
        from search.indexer import build_document
        loras = [_make_lora(None), _make_lora("valid")]
        doc = build_document(_make_image(), _make_generation(), loras, _make_review(), _make_storage())
        assert doc["loras"] == ["valid"]

    def test_empty_loras(self):
        from search.indexer import build_document
        doc = build_document(_make_image(), _make_generation(), [], _make_review(), _make_storage())
        assert doc["loras"] == []


class TestEnsureBucket:
    def test_creates_bucket_and_applies_policy_when_new(self):
        from unittest.mock import patch, MagicMock
        from services.image_importer import ensure_bucket

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False

        with patch("services.image_importer.minio_client", mock_client):
            ensure_bucket("new-bucket")

        mock_client.make_bucket.assert_called_once_with("new-bucket")
        mock_client.set_bucket_policy.assert_called_once()
        policy_arg = mock_client.set_bucket_policy.call_args[0][1]
        assert "new-bucket" in policy_arg

    def test_skips_create_when_bucket_exists(self):
        from unittest.mock import patch, MagicMock
        from services.image_importer import ensure_bucket

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True

        with patch("services.image_importer.minio_client", mock_client):
            ensure_bucket("existing-bucket")

        mock_client.make_bucket.assert_not_called()
        mock_client.set_bucket_policy.assert_called_once()

    def test_tolerates_already_exists_s3_error(self):
        from unittest.mock import patch, MagicMock

        class FakeS3Error(Exception):
            def __init__(self, code):
                self.code = code

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        mock_client.make_bucket.side_effect = FakeS3Error("BucketAlreadyOwnedByYou")

        with (
            patch("services.image_importer.minio_client", mock_client),
            patch("services.image_importer.S3Error", FakeS3Error),
        ):
            from services.image_importer import ensure_bucket
            ensure_bucket("race-bucket")

        mock_client.set_bucket_policy.assert_called_once()

    def test_reraises_unexpected_s3_error(self):
        from unittest.mock import patch, MagicMock

        class FakeS3Error(Exception):
            def __init__(self, code):
                self.code = code

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        mock_client.make_bucket.side_effect = FakeS3Error("InternalError")

        with (
            patch("services.image_importer.minio_client", mock_client),
            patch("services.image_importer.S3Error", FakeS3Error),
        ):
            from services.image_importer import ensure_bucket
            with pytest.raises(FakeS3Error):
                ensure_bucket("bad-bucket")
