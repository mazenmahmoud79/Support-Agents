#!/usr/bin/env python3
"""
Tenant Provisioning Script — Zada Support Agents

Creates a new tenant with:
  - Tenant record in PostgreSQL
  - Demo user for dashboard login
  - Qdrant collection for vector storage

Usage:
  python provision_tenant.py "Company Name"
  python provision_tenant.py "Company Name" --slug my-company

Requires DATABASE_URL and QDRANT_HOST/QDRANT_PORT env vars (reads from ../.env).
"""
import argparse
import os
import sys
import secrets

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.db.session import get_db, init_db
from app.models.database import Tenant, DemoUser
from app.core.security import generate_api_key
from datetime import datetime


def generate_demo_id():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "DEMO-" + ''.join(secrets.choice(chars) for _ in range(6))


def provision_tenant(name: str, slug: str = None):
    """Create a tenant, demo user, and Qdrant collection."""

    init_db()
    db = next(get_db())

    try:
        # Generate identifiers
        name_slug = name.lower().replace(" ", "_").replace("-", "_")
        tenant_id = f"tenant_{name_slug}_{secrets.token_hex(3)}"
        slug = slug or name.lower().replace(" ", "-").replace("_", "-")
        api_key = generate_api_key()
        demo_id = generate_demo_id()

        # Ensure unique demo_id
        while db.query(DemoUser).filter(DemoUser.demo_id == demo_id).first():
            demo_id = generate_demo_id()

        # Check for duplicate slug
        if db.query(Tenant).filter(Tenant.slug == slug).first():
            print(f"ERROR: Tenant with slug '{slug}' already exists.")
            sys.exit(1)

        # Create tenant
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            api_key=api_key,
            is_active=1,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # Create demo user
        demo_user = DemoUser(
            demo_id=demo_id,
            tenant_id=tenant_id,
            name=f"Admin for {name}",
            is_active=1,
            created_at=datetime.utcnow(),
        )
        db.add(demo_user)
        db.commit()

        # Create Qdrant collection
        try:
            from app.services.vector_store import get_vector_store
            from app.config import settings
            vs = get_vector_store()
            collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}{tenant_id}"
            vs.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "size": settings.EMBEDDING_DIMENSION,
                    "distance": "Cosine",
                },
            )
            print(f"✓ Qdrant collection: {collection_name}")
        except Exception as e:
            print(f"⚠ Qdrant collection creation failed (can be created on first upload): {e}")

        # Output results
        print()
        print("=" * 60)
        print(f"  Tenant provisioned successfully!")
        print("=" * 60)
        print(f"  Name:       {name}")
        print(f"  Tenant ID:  {tenant_id}")
        print(f"  Slug:       {slug}")
        print(f"  Demo ID:    {demo_id}")
        print(f"  API Key:    {api_key}")
        print("=" * 60)
        print()
        print("Next steps:")
        print(f"  1. Login at the dashboard with Demo ID: {demo_id}")
        print(f"  2. Upload knowledge base documents")
        print(f"  3. Embed the chat widget using slug: {slug}")
        print()

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Provision a new Zada tenant")
    parser.add_argument("name", help="Tenant/company name")
    parser.add_argument("--slug", help="Custom URL slug (auto-generated if omitted)")
    args = parser.parse_args()

    provision_tenant(args.name, args.slug)


if __name__ == "__main__":
    main()
