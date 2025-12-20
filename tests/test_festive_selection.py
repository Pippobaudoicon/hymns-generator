#!/usr/bin/env python3
"""Test script to verify festive hymns can be selected when appropriate."""

import logging

from hymns.models import FestivityType
from hymns.service import HymnService

# Setup logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise


def test_festive_selection_multiple_times():
    """Test that festive hymns can be selected when appropriate."""

    service = HymnService("data/italian_hymns_full.json")

    print("=== TESTING FESTIVE HYMN SELECTION (Multiple attempts) ===\n")

    # Test Christmas selections
    print("Testing Christmas Sunday selections (10 attempts):")
    natale_found_count = 0
    for i in range(10):
        hymns = service.get_hymns(
            prima_domenica=False,
            domenica_festiva=True,
            tipo_festivita=FestivityType.NATALE,
        )
        for hymn in hymns:
            if hymn.category.lower() == "natale":
                print(
                    f"  Attempt {i+1}: Found natale hymn #{hymn.number}: {hymn.title}"
                )
                natale_found_count += 1
                break

    print(f"Found natale hymns in {natale_found_count}/10 attempts")

    # Test Easter selections
    print("\nTesting Easter Sunday selections (10 attempts):")
    pasqua_found_count = 0
    for i in range(10):
        hymns = service.get_hymns(
            prima_domenica=False,
            domenica_festiva=True,
            tipo_festivita=FestivityType.PASQUA,
        )
        for hymn in hymns:
            if hymn.category.lower() == "pasqua":
                print(
                    f"  Attempt {i+1}: Found pasqua hymn #{hymn.number}: {hymn.title}"
                )
                pasqua_found_count += 1
                break

    print(f"Found pasqua hymns in {pasqua_found_count}/10 attempts")

    # Test that we can get specific festive hymns by filtering the pool
    print("\nTesting available festive hymns by examining the filtered pools:")

    # Christmas
    other_hymns = service._get_other_hymns(
        domenica_festiva=True, tipo_festivita=FestivityType.NATALE
    )
    natale_in_pool = []
    for hymn in other_hymns:
        if hymn.category.lower() == "natale" or "natale" in [
            tag.lower() for tag in hymn.tags
        ]:
            natale_in_pool.append(hymn)

    print(f"Available natale hymns in Christmas pool: {len(natale_in_pool)}")
    for hymn in natale_in_pool:
        source = "category" if hymn.category.lower() == "natale" else "tag"
        print(
            f"  #{hymn.number}: {hymn.title} (Category: {hymn.category}) [from {source}]"
        )

    # Easter
    other_hymns = service._get_other_hymns(
        domenica_festiva=True, tipo_festivita=FestivityType.PASQUA
    )
    pasqua_in_pool = []
    for hymn in other_hymns:
        if hymn.category.lower() == "pasqua" or "pasqua" in [
            tag.lower() for tag in hymn.tags
        ]:
            pasqua_in_pool.append(hymn)

    print(f"\nAvailable pasqua hymns in Easter pool: {len(pasqua_in_pool)}")
    for hymn in pasqua_in_pool:
        source = "category" if hymn.category.lower() == "pasqua" else "tag"
        print(
            f"  #{hymn.number}: {hymn.title} (Category: {hymn.category}) [from {source}]"
        )

    # Check Sacramento pools
    print("\nChecking Sacramento hymn pools:")

    # Christmas Sacramento pool
    sacramento_natale = service._get_sacramento_hymns(
        domenica_festiva=True, tipo_festivita=FestivityType.NATALE
    )
    natale_sacramento = []
    for hymn in sacramento_natale:
        if hymn.category.lower() == "natale" or "natale" in [
            tag.lower() for tag in hymn.tags
        ]:
            natale_sacramento.append(hymn)

    print(
        f"Sacramento hymns with natale category/tag available for Christmas: {len(natale_sacramento)}"
    )
    for hymn in natale_sacramento:
        source = "category" if hymn.category.lower() == "natale" else "tag"
        print(f"  #{hymn.number}: {hymn.title} [from {source}]")

    # Easter Sacramento pool
    sacramento_pasqua = service._get_sacramento_hymns(
        domenica_festiva=True, tipo_festivita=FestivityType.PASQUA
    )
    pasqua_sacramento = []
    for hymn in sacramento_pasqua:
        if hymn.category.lower() == "pasqua" or "pasqua" in [
            tag.lower() for tag in hymn.tags
        ]:
            pasqua_sacramento.append(hymn)

    print(
        f"Sacramento hymns with pasqua category/tag available for Easter: {len(pasqua_sacramento)}"
    )
    for hymn in pasqua_sacramento:
        source = "category" if hymn.category.lower() == "pasqua" else "tag"
        print(f"  #{hymn.number}: {hymn.title} [from {source}]")


if __name__ == "__main__":
    test_festive_selection_multiple_times()
