"""Supabase helpers for database and storage usage."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from supabase import Client, create_client
from supabase.storage.file_options import FileOptions


def _resolve_supabase_credentials() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ImproperlyConfigured(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) to use Supabase."
        )
    return url, key


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client instance."""
    url, key = _resolve_supabase_credentials()
    return create_client(url, key)


def upload_bytes(
    *,
    path: str,
    content: bytes,
    bucket: str | None = None,
    content_type: str | None = None,
    upsert: bool = True,
) -> str:
    """
    Upload a bytes payload to Supabase storage and return a public URL.

    Use for small blobs (images, docs) when you already have the content in memory.
    """
    client = get_supabase_client()
    storage = client.storage.from_(bucket or os.getenv("SUPABASE_STORAGE_BUCKET", "media"))
    options = FileOptions(upsert=upsert, content_type=content_type)
    storage.upload(path, content, options=options)
    return storage.get_public_url(path)


def create_signed_url(
    *,
    path: str,
    bucket: str | None = None,
    expires_in: int = 3600,
) -> str:
    """Return a time-limited signed URL for a stored object."""
    client = get_supabase_client()
    storage = client.storage.from_(bucket or os.getenv("SUPABASE_STORAGE_BUCKET", "media"))
    result: dict[str, Any] = storage.create_signed_url(path, expires_in=expires_in)
    return result.get("signedURL") or result.get("signedUrl") or ""
