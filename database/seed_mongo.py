#!/usr/bin/env python3
"""
LibraCore — MongoDB Seed & JSON Export Utility
Exports all 8 collections into database/mongodb_collections.json for 1-click MongoDB Compass import.
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'application'))
from mongo_manager import get_mongo_db, seed_mongo_database

def export_collections_json():
    print("[1/2] Seeding MongoDB collections...")
    seed_mongo_database(force=True)
    
    db = get_mongo_db()
    collections = ['categories', 'authors', 'librarians', 'books', 'members', 'issues', 'fines', 'reservations']
    
    dump = {}
    for coll_name in collections:
        docs = list(db[coll_name].find({}))
        # Convert any non-serializable fields
        for d in docs:
            if "_id" in d and not isinstance(d["_id"], (int, str, float)):
                d["_id"] = str(d["_id"])
        dump[coll_name] = docs
        print(f"  - Collection '{coll_name}': {len(docs)} documents")

    out_path = os.path.join(os.path.dirname(__file__), 'mongodb_collections.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dump, f, indent=2, default=str)

    print(f"[2/2] Saved full MongoDB collection dump to: {out_path}")

if __name__ == '__main__':
    export_collections_json()
