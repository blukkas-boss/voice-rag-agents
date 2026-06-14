"""Milvus vector store adapter.

Satisfies ``voice_rag_agents.dataflows.interfaces.VectorStore``.

Requires ``pymilvus``. If the package is absent the module still imports
but every method raises a clearinstall error. This lets tests import the
module and use ``pytest.importorskip`` for conditional integration tests.

Adapter pattern: collection create / upsert / search / delete by doc hash.
"""

from __future__ import annotations

from voice_rag_agents.dataflows.vector_records import (
    SearchRequest,
    SearchResult,
    VectorRecord,
)

try:
    from pymilvus import (  # type: ignore[import-untyped]
        CollectionSchema,
        DataType,
        FieldSchema,
        MilvusClient,
        utility,
    )

    _MILVUS_AVAILABLE = True
except ImportError:
    _MILVUS_AVAILABLE = False


class MilvusAdapter:
    """Milvus vector store adapter.

    Uses the v2 ``MilvusClient`` (REST/gRPC) interface.
    """

    def __init__(self, uri: str = "http://localhost:19530", timeout: float = 30.0) -> None:
        if not _MILVUS_AVAILABLE:
            raise ImportError(
                "pymilvus is required for Milvus support."
                " Install with: pip install pymilvus"
            )
        self._uri = uri
        self._timeout = timeout
        self._client: MilvusClient | None = None

    def _get_client(self) -> "MilvusClient":
        if self._client is None:
            self._client = MilvusClient(uri=self._uri, timeout=self._timeout)
        return self._client

    # -- VectorStore interface -----------------------------------------------

    def health(self) -> dict:
        try:
            client = self._get_client()
            # list_collections() is a lightweight connectivity check
            colls = client.list_collections()
            return {"status": "ok", "collections": colls}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": str(exc)[:300]}

    def ensure_collection(self, name: str, dimension: int) -> None:
        client = self._get_client()
        if utility.has_collection(name):
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="metadata_json", dtype=DataType.VARCHAR, max_length=4096),
        ]
        schema = CollectionSchema(fields=fields)
        client.create_collection(collection_name=name, schema=schema)
        # Create HNSW index for the vector field
        index_params = client.prepare_index_params()
        index_params.add_index(field_name="vector", index_type="HNSW", metric_type="COSINE", params={"M": 8, "efConstruction": 64})
        client.create_index(collection_name=name, index_params=index_params)

    def upsert(self, collection: str, records: list[VectorRecord]) -> dict:
        client = self._get_client()
        import json as _json

        rows = []
        for rec in records:
            rows.append(
                {
                    "id": rec.id,
                    "document_id": rec.document_id,
                    "chunk_id": rec.chunk_id,
                    "chunk_text": rec.chunk_text,
                    "vector": rec.vector,
                    "metadata_json": _json.dumps(rec.metadata),
                }
            )
        if not rows:
            return {"upserted": 0}
        client.insert(collection_name=collection, data=rows)
        client.flush([collection])
        return {"upserted": len(rows)}

    def search(
        self, collection: str, request: SearchRequest
    ) -> list[SearchResult]:
        import json as _json

        client = self._get_client()
        output_fields = request.output_fields or [
            "chunk_id", "chunk_text", "document_id", "metadata_json",
        ]
        try:
            resp = client.search(
                collection_name=collection,
                data=[request.query_vector],
                limit=request.top_k,
                output_fields=output_fields,
                filter=_build_milvus_filter(request.filters),
            )
        except Exception:  # noqa: BLE001 — return empty on any failure
            return []

        results: list[SearchResult] = []
        hits = resp[0] if resp else []
        for hit in hits:
            entity = hit.get("entity", {})
            md: dict = {}
            raw = entity.get("metadata_json", "{}")
            try:
                md = _json.loads(raw) if isinstance(raw, str) else (raw or {})
            except ValueError:
                md = {}
            results.append(
                SearchResult(
                    id=str(entity.get("id", "")),
                    chunk_id=str(entity.get("chunk_id", "")),
                    chunk_text=str(entity.get("chunk_text", "")),
                    score=hit.get("distance", 0.0),
                    metadata=md,
                    document_id=str(entity.get("document_id", "")),
                )
            )
        return results

    def delete_by_document_id(self, collection: str, document_id: str) -> dict:
        client = self._get_client()
        try:
            result = client.delete(
                collection_name=collection,
                filter=f'document_id == "{document_id}"',
            )
            return {"deleted": result.get("delete_count", 0)}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)[:300]}


def _build_milvus_filter(filters: dict | None) -> str | None:
    """Convert a flat ``{key: value}`` dict to a Milvus filter expression."""
    if not filters:
        return None
    parts = [f'metadata_json["{k}"] == "{v}"' for k, v in filters.items()]
    if len(parts) == 1:
        return parts[0]
    return " and ".join(parts)
