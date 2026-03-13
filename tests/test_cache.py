"""Tests for core.cache module — IntelligenceCache and CodePattern."""

from pathlib import Path

import pytest

from core.cache import CodePattern, IntelligenceCache


@pytest.fixture()
def cache(tmp_path):
    return IntelligenceCache(cache_dir=tmp_path / "cache", use_transformers=False)


@pytest.fixture()
def sample_pattern():
    return CodePattern(
        pattern_id="auth-jwt",
        code="def authenticate(): ...",
        metadata={"stack": "python-fastapi", "category": "authentication", "name": "JWT Auth"},
        context_hash="abc123",
        success_rate=0.8,
        usage_count=5,
        tags=["auth", "jwt"],
    )


# -- CodePattern --

class TestCodePattern:
    def test_init(self):
        p = CodePattern(
            pattern_id="p1", code="x", metadata={}, context_hash="h1"
        )
        assert p.tags == []
        assert p.context_vector is None

    def test_init_empty_vector(self):
        p = CodePattern(
            pattern_id="p1", code="x", metadata={}, context_hash="h1",
            context_vector=[],
        )
        assert p.context_vector is None

    def test_init_with_vector(self):
        p = CodePattern(
            pattern_id="p1", code="x", metadata={}, context_hash="h1",
            context_vector=[0.1, 0.2],
        )
        assert p.context_vector == [0.1, 0.2]


# -- IntelligenceCache init --

class TestIntelligenceCacheInit:
    def test_init_creates_dir(self, tmp_path):
        cache_dir = tmp_path / "new_cache"
        cache = IntelligenceCache(cache_dir=cache_dir, use_transformers=False)
        assert cache_dir.exists()
        assert cache.db_path.exists()

    def test_init_no_transformers(self, cache):
        assert cache.use_transformers is False
        assert cache.embedding_model is None

    def test_init_force_no_ia(self, tmp_path):
        cache = IntelligenceCache(cache_dir=tmp_path, use_transformers=True, force_no_ia=True)
        assert cache.use_transformers is False


# -- store_pattern / get_pattern --

class TestStoreGetPattern:
    def test_store_and_retrieve(self, cache, sample_pattern):
        cache.store_pattern(sample_pattern)
        retrieved = cache.get_pattern("auth-jwt")
        assert retrieved is not None
        assert retrieved.pattern_id == "auth-jwt"
        assert retrieved.code == "def authenticate(): ..."
        assert retrieved.success_rate == 0.8

    def test_get_nonexistent(self, cache):
        result = cache.get_pattern("nonexistent")
        assert result is None

    def test_store_overwrites(self, cache, sample_pattern):
        cache.store_pattern(sample_pattern)
        sample_pattern.code = "updated code"
        cache.store_pattern(sample_pattern)
        retrieved = cache.get_pattern("auth-jwt")
        assert retrieved.code == "updated code"


# -- search_similar (Levenshtein mode) --

class TestSearchSimilar:
    def test_search_empty_cache(self, cache):
        results = cache.search_similar({"stack": "python"})
        assert results == []

    def test_search_with_patterns(self, cache, sample_pattern):
        cache.store_pattern(sample_pattern)
        results = cache.search_similar({"stack": "python-fastapi", "category": "authentication"})
        assert len(results) >= 1
        assert results[0].pattern_id == "auth-jwt"

    def test_search_limit(self, cache):
        for i in range(10):
            p = CodePattern(
                pattern_id=f"p{i}", code=f"code{i}",
                metadata={"stack": "python", "category": "api"},
                context_hash=f"h{i}", success_rate=0.5,
            )
            cache.store_pattern(p)
        results = cache.search_similar({"stack": "python"}, limit=3)
        assert len(results) <= 3


# -- update_success_rate --

class TestUpdateSuccessRate:
    def test_update_existing(self, cache, sample_pattern):
        cache.store_pattern(sample_pattern)
        cache.update_success_rate("auth-jwt", True)
        updated = cache.get_pattern("auth-jwt")
        assert updated.usage_count == 6

    def test_update_nonexistent(self, cache):
        # Should not raise
        cache.update_success_rate("nonexistent", True)

    def test_update_first_usage(self, cache):
        p = CodePattern(
            pattern_id="new", code="x", metadata={}, context_hash="h",
            success_rate=0.0, usage_count=0,
        )
        cache.store_pattern(p)
        cache.update_success_rate("new", True)
        updated = cache.get_pattern("new")
        assert updated.usage_count == 1
        assert updated.success_rate == 1.0


# -- get_top_patterns --

class TestGetTopPatterns:
    def test_empty(self, cache):
        assert cache.get_top_patterns() == []

    def test_with_patterns(self, cache):
        for i in range(5):
            p = CodePattern(
                pattern_id=f"p{i}", code=f"c{i}", metadata={},
                context_hash=f"h{i}", success_rate=i * 0.2,
            )
            cache.store_pattern(p)
        top = cache.get_top_patterns(limit=3)
        assert len(top) == 3
        assert top[0].success_rate >= top[1].success_rate


# -- record_token_usage / get_token_usage_stats --

class TestTokenUsage:
    def test_record_and_get(self, cache):
        cache.record_token_usage("generate_prd", tokens_input=100, tokens_output=50, tokens_saved=30, cost_usd=0.01)
        stats = cache.get_token_usage_stats()
        assert stats["count"] == 1
        assert stats["total_input"] == 100
        assert stats["total_saved"] == 30

    def test_get_by_operation(self, cache):
        cache.record_token_usage("op1", tokens_input=10)
        cache.record_token_usage("op2", tokens_input=20)
        stats = cache.get_token_usage_stats("op1")
        assert stats["count"] == 1
        assert stats["total_input"] == 10

    def test_get_empty(self, cache):
        stats = cache.get_token_usage_stats()
        assert stats["count"] == 0


# -- record_validation --

class TestRecordValidation:
    def test_record(self, cache):
        cache.record_validation("prp", "F0.md", "pass", errors=[], warnings=["minor"])

    def test_record_with_errors(self, cache):
        cache.record_validation("prp", "F1.md", "fail", errors=["missing field"])


# -- record_metric / get_metrics --

class TestMetrics:
    def test_record_and_get(self, cache):
        cache.record_metric("coverage", "test_coverage", 85.0, {"module": "core"})
        metrics = cache.get_metrics()
        assert len(metrics) == 1
        assert metrics[0]["value"] == 85.0

    def test_get_by_type(self, cache):
        cache.record_metric("coverage", "cov1", 80.0)
        cache.record_metric("performance", "perf1", 100.0)
        cov = cache.get_metrics("coverage")
        assert len(cov) == 1
        assert cov[0]["name"] == "cov1"

    def test_get_empty(self, cache):
        assert cache.get_metrics() == []


# -- _hash_context --

class TestHashContext:
    def test_deterministic(self, cache):
        h1 = cache._hash_context({"a": 1})
        h2 = cache._hash_context({"a": 1})
        assert h1 == h2

    def test_different_contexts(self, cache):
        h1 = cache._hash_context({"a": 1})
        h2 = cache._hash_context({"b": 2})
        assert h1 != h2


# -- _create_context_text --

class TestCreateContextText:
    def test_with_stack(self, cache):
        text = cache._create_context_text({"stack": ["python", "fastapi"]})
        assert "python" in text

    def test_with_category(self, cache):
        text = cache._create_context_text({"category": "auth"})
        assert "auth" in text

    def test_with_requirements_list(self, cache):
        text = cache._create_context_text({"requirements": ["r1", "r2"]})
        assert "r1" in text

    def test_with_requirements_str(self, cache):
        text = cache._create_context_text({"requirements": "single req"})
        assert "single req" in text

    def test_with_description(self, cache):
        text = cache._create_context_text({"description": "A cool feature"})
        assert "A cool feature" in text

    def test_with_metadata(self, cache):
        text = cache._create_context_text({"metadata": {"name": "JWT", "complexity": "medium"}})
        assert "JWT" in text
        assert "medium" in text

    def test_empty(self, cache):
        text = cache._create_context_text({})
        assert text == ""


# -- _calculate_levenshtein --

class TestLevenshtein:
    def test_identical(self, cache):
        assert cache._calculate_levenshtein("hello", "hello") == 1.0

    def test_empty_both(self, cache):
        assert cache._calculate_levenshtein("", "") == 1.0

    def test_empty_one(self, cache):
        assert cache._calculate_levenshtein("hello", "") == 0.0

    def test_similar(self, cache):
        sim = cache._calculate_levenshtein("python", "pythons")
        assert 0.8 < sim < 1.0

    def test_different(self, cache):
        sim = cache._calculate_levenshtein("abc", "xyz")
        assert sim < 0.5


# -- Embedding model property (lazy load) --

class TestEmbeddingModelProperty:
    def test_no_transformers_returns_none(self, cache):
        """When use_transformers=False, embedding_model should be None."""
        assert cache.embedding_model is None

    def test_use_transformers_but_load_fails(self, tmp_path):
        """When use_transformers=True but model fails to load, falls back gracefully."""
        import unittest.mock as um
        with um.patch("core.cache.TRANSFORMERS_AVAILABLE", True), \
             um.patch("core.cache.SentenceTransformer", side_effect=Exception("model not found")):
            c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=True)
            # Force the property to trigger lazy load
            model = c.embedding_model
            assert model is None
            assert c.use_transformers is False

    def test_use_transformers_loads_model(self, tmp_path):
        """When transformers available and model loads, embedding_model is set."""
        import unittest.mock as um
        mock_model = um.MagicMock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_st_cls = um.MagicMock(return_value=mock_model)
        with um.patch("core.cache.TRANSFORMERS_AVAILABLE", True), \
             um.patch("core.cache.SentenceTransformer", mock_st_cls):
            c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=True)
            model = c.embedding_model
            assert model is mock_model
            assert c.embedding_dim == 3

    def test_use_transformers_loads_from_local_path(self, tmp_path):
        """When local model path exists, loads from it."""
        import unittest.mock as um
        cache_dir = tmp_path / "c"
        cache_dir.mkdir(parents=True)
        models_dir = cache_dir / "models" / "all-MiniLM-L6-v2"
        models_dir.mkdir(parents=True)
        mock_model = um.MagicMock()
        mock_model.encode.return_value = [0.5]
        mock_st_cls = um.MagicMock(return_value=mock_model)
        with um.patch("core.cache.TRANSFORMERS_AVAILABLE", True), \
             um.patch("core.cache.SentenceTransformer", mock_st_cls):
            c = IntelligenceCache(cache_dir=cache_dir, use_transformers=True)
            model = c.embedding_model
            assert model is mock_model
            # Should have been called with the local path string
            mock_st_cls.assert_called_once_with(str(models_dir))


# -- _generate_embedding --

class TestGenerateEmbedding:
    def test_no_transformers_returns_empty(self, cache):
        result = cache._generate_embedding("hello")
        assert result == []

    def test_with_mocked_transformers(self, tmp_path):
        """Full embedding generation + SQLite caching cycle."""
        import unittest.mock as um
        import numpy as np

        mock_model = um.MagicMock()
        embedding_array = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_model.encode.return_value = embedding_array
        mock_model.__len__ = lambda self: 3

        mock_st_cls = um.MagicMock(return_value=mock_model)
        with um.patch("core.cache.TRANSFORMERS_AVAILABLE", True), \
             um.patch("core.cache.SentenceTransformer", mock_st_cls):
            c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=True)
            c._embedding_model = mock_model
            c.embedding_dim = 3

            # First call generates and caches
            result = c._generate_embedding("test text", cache_key="key1")
            assert len(result) == 3
            assert abs(result[0] - 0.1) < 0.01

            # Second call should hit cache
            result2 = c._generate_embedding("test text", cache_key="key1")
            assert len(result2) == 3

    def test_generate_embedding_no_cache_key(self, tmp_path):
        """When cache_key is None, uses text hash."""
        import unittest.mock as um
        import numpy as np

        mock_model = um.MagicMock()
        mock_model.encode.return_value = np.array([0.5], dtype=np.float32)
        mock_st_cls = um.MagicMock(return_value=mock_model)
        with um.patch("core.cache.TRANSFORMERS_AVAILABLE", True), \
             um.patch("core.cache.SentenceTransformer", mock_st_cls):
            c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=True)
            c._embedding_model = mock_model
            c.embedding_dim = 1
            result = c._generate_embedding("text", cache_key=None)
            assert len(result) == 1

    def test_generate_embedding_encode_error(self, tmp_path):
        """When encode raises, returns empty list."""
        import unittest.mock as um

        mock_model = um.MagicMock()
        mock_model.encode.side_effect = RuntimeError("GPU error")
        mock_st_cls = um.MagicMock(return_value=mock_model)
        with um.patch("core.cache.TRANSFORMERS_AVAILABLE", True), \
             um.patch("core.cache.SentenceTransformer", mock_st_cls):
            c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=True)
            c._embedding_model = mock_model
            c.embedding_dim = 3
            result = c._generate_embedding("fail text")
            assert result == []


# -- _vector_search --

class TestVectorSearch:
    def test_vector_search_empty_embedding(self, tmp_path):
        """When embedding generation returns empty, returns empty results."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        # Manually call _vector_search — it needs use_transformers and model
        with um.patch.object(c, "_generate_embedding", return_value=[]):
            results = c._vector_search({"stack": "python"}, "python")
            assert results == []

    def test_vector_search_with_patterns(self, tmp_path):
        """Vector search with mocked embeddings and stored patterns."""
        import unittest.mock as um
        import numpy as np

        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        # Store a pattern
        p = CodePattern(
            pattern_id="p1", code="x", metadata={"stack": "python"},
            context_hash="h1", success_rate=0.9,
        )
        c.store_pattern(p)

        # Store a fake embedding for pattern p1
        embedding = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        import sqlite3
        with sqlite3.connect(c.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO embeddings (cache_key, text_hash, embedding, dimension) VALUES (?, ?, ?, ?)",
                ("p1", "fake", embedding.tobytes(), 3),
            )
            conn.commit()

        query_vec = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        with um.patch.object(c, "_generate_embedding", return_value=list(query_vec)):
            results = c._vector_search({"stack": "python"}, "python")
            assert len(results) >= 1
            score, pattern = results[0]
            assert pattern.pattern_id == "p1"
            assert score > 0

    def test_vector_search_pattern_no_embedding(self, tmp_path):
        """Pattern without embedding gets similarity 0."""
        import unittest.mock as um
        import numpy as np

        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        p = CodePattern(
            pattern_id="p2", code="y", metadata={"stack": "go"},
            context_hash="h2", success_rate=0.5,
        )
        c.store_pattern(p)

        query_vec = np.array([0.1, 0.2], dtype=np.float32)
        with um.patch.object(c, "_generate_embedding", return_value=list(query_vec)):
            results = c._vector_search({"stack": "go"}, "go")
            assert len(results) >= 1
            score, _ = results[0]
            # Score should be based on success_rate * 0.3 only (similarity=0)
            assert score == pytest.approx(0.5 * 0.3, abs=0.01)

    def test_vector_search_db_error(self, tmp_path):
        """DB error during vector search returns empty."""
        import unittest.mock as um
        import numpy as np

        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        query_vec = [0.1, 0.2]
        with um.patch.object(c, "_generate_embedding", return_value=query_vec), \
             um.patch("sqlite3.connect", side_effect=Exception("DB locked")):
            results = c._vector_search({"stack": "x"}, "x")
            assert results == []


# -- store_pattern with transformers --

class TestStorePatternTransformers:
    def test_store_generates_embedding(self, tmp_path):
        """When use_transformers=True, store_pattern generates embedding."""
        import unittest.mock as um

        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        c.use_transformers = True  # Force flag
        p = CodePattern(
            pattern_id="tp1", code="code", metadata={"stack": "python", "category": "api"},
            context_hash="h", context_vector=None,
        )
        with um.patch.object(c, "_generate_embedding", return_value=[0.1, 0.2]) as mock_gen:
            c.store_pattern(p)
            mock_gen.assert_called_once()


# -- Error paths for DB operations --

class TestDBErrorPaths:
    def test_store_pattern_db_error(self, tmp_path):
        """store_pattern handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        p = CodePattern(pattern_id="err", code="x", metadata={}, context_hash="h")
        with um.patch("sqlite3.connect", side_effect=Exception("disk full")):
            # Should not raise
            c.store_pattern(p)

    def test_get_pattern_db_error(self, tmp_path):
        """get_pattern handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("corrupt")):
            result = c.get_pattern("any")
            assert result is None

    def test_update_success_rate_db_error(self, tmp_path):
        """update_success_rate handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("locked")):
            c.update_success_rate("any", True)

    def test_get_top_patterns_db_error(self, tmp_path):
        """get_top_patterns handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("error")):
            result = c.get_top_patterns()
            assert result == []

    def test_record_token_usage_db_error(self, tmp_path):
        """record_token_usage handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("error")):
            c.record_token_usage("op", tokens_input=10)

    def test_get_token_usage_stats_db_error(self, tmp_path):
        """get_token_usage_stats handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("error")):
            result = c.get_token_usage_stats()
            assert result["count"] == 0

    def test_record_validation_db_error(self, tmp_path):
        """record_validation handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("error")):
            c.record_validation("prp", "f.md", "pass")

    def test_record_metric_db_error(self, tmp_path):
        """record_metric handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("error")):
            c.record_metric("cov", "test", 90.0)

    def test_get_metrics_db_error(self, tmp_path):
        """get_metrics handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("error")):
            result = c.get_metrics()
            assert result == []

    def test_levenshtein_search_db_error(self, tmp_path):
        """_levenshtein_search handles DB errors gracefully."""
        import unittest.mock as um
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        with um.patch("sqlite3.connect", side_effect=Exception("error")):
            result = c._levenshtein_search("text")
            assert result == []

    def test_levenshtein_search_empty_text(self, tmp_path):
        """_levenshtein_search with empty text returns empty."""
        c = IntelligenceCache(cache_dir=tmp_path / "c", use_transformers=False)
        result = c._levenshtein_search("")
        assert result == []


# -- search_similar with context_text fallback --

class TestSearchSimilarFallback:
    def test_search_with_empty_context_text(self, cache, sample_pattern):
        """When _create_context_text returns empty, falls back to JSON."""
        cache.store_pattern(sample_pattern)
        results = cache.search_similar({})
        # Should still work with JSON fallback
        assert isinstance(results, list)
