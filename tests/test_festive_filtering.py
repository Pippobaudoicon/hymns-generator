#!/usr/bin/env python3
"""Test script to verify strict festive hymn filtering."""

import logging
from hymns.service import HymnService
from hymns.models import FestivityType

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_festive_filtering():
    """Test that festive hymns are strictly filtered based on tipo_festivita."""
    
    # Initialize service
    service = HymnService("data/italian_hymns_full.json")
    
    print("=== TESTING FESTIVE HYMN FILTERING ===\n")
    
    # Test 1: Normal Sunday (no festivity) should exclude all festive hymns
    print("1. Normal Sunday (no festivity):")
    hymns = service.get_hymns(prima_domenica=False, domenica_festiva=False)
    
    festive_found = []
    for hymn in hymns:
        category_lower = hymn.category.lower()
        if category_lower == 'natale' or category_lower == 'pasqua':
            festive_found.append(f"  - #{hymn.number}: {hymn.title} (category: {hymn.category})")
    
    if festive_found:
        print("  ❌ FAILED: Found festive hymns in normal Sunday:")
        for hymn in festive_found:
            print(hymn)
    else:
        print("  ✅ PASSED: No festive hymns found")
    
    # Test 2: Christmas Sunday should only include natale hymns, not pasqua
    print("\n2. Christmas Sunday (tipo_festivita=natale):")
    hymns = service.get_hymns(prima_domenica=False, domenica_festiva=True, tipo_festivita=FestivityType.NATALE)
    
    pasqua_found = []
    natale_found = []
    for hymn in hymns:
        category_lower = hymn.category.lower()
        if category_lower == 'pasqua':
            pasqua_found.append(f"  - #{hymn.number}: {hymn.title} (category: {hymn.category})")
        if category_lower == 'natale':
            natale_found.append(f"  - #{hymn.number}: {hymn.title} (category: {hymn.category})")
    
    if pasqua_found:
        print("  ❌ FAILED: Found pasqua hymns in Christmas Sunday:")
        for hymn in pasqua_found:
            print(hymn)
    else:
        print("  ✅ PASSED: No pasqua hymns found")
    
    if natale_found:
        print("  ✅ GOOD: Found natale hymns as expected:")
        for hymn in natale_found:
            print(hymn)
    else:
        print("  ⚠️  WARNING: No natale hymns found (might be due to random selection)")
    
    # Test 3: Easter Sunday should only include pasqua hymns, not natale
    print("\n3. Easter Sunday (tipo_festivita=pasqua):")
    hymns = service.get_hymns(prima_domenica=False, domenica_festiva=True, tipo_festivita=FestivityType.PASQUA)
    
    natale_found = []
    pasqua_found = []
    for hymn in hymns:
        category_lower = hymn.category.lower()
        if category_lower == 'natale':
            natale_found.append(f"  - #{hymn.number}: {hymn.title} (category: {hymn.category})")
        if category_lower == 'pasqua':
            pasqua_found.append(f"  - #{hymn.number}: {hymn.title} (category: {hymn.category})")
    
    if natale_found:
        print("  ❌ FAILED: Found natale hymns in Easter Sunday:")
        for hymn in natale_found:
            print(hymn)
    else:
        print("  ✅ PASSED: No natale hymns found")
    
    if pasqua_found:
        print("  ✅ GOOD: Found pasqua hymns as expected:")
        for hymn in pasqua_found:
            print(hymn)
    else:
        print("  ⚠️  WARNING: No pasqua hymns found (might be due to random selection)")
    
    # Test 4: Verify Sacramento hymn position and filtering
    print("\n4. Checking Sacramento hymn filtering:")
    
    # Christmas Sunday
    print("  Christmas Sunday:")
    hymns = service.get_hymns(prima_domenica=False, domenica_festiva=True, tipo_festivita=FestivityType.NATALE)
    sacramento_hymn = hymns[1]  # Second position should be Sacramento
    print(f"    Sacramento hymn: #{sacramento_hymn.number}: {sacramento_hymn.title}")
    print(f"    Category: {sacramento_hymn.category}")
    print(f"    Tags: {sacramento_hymn.tags}")
    
    # Check if it has inappropriate festive tags
    category_lower = sacramento_hymn.category.lower()
    if category_lower == 'pasqua':
        print("    ❌ FAILED: Sacramento hymn is from pasqua category in Christmas Sunday")
    else:
        print("    ✅ PASSED: Sacramento hymn is not from inappropriate festive category")
    
    # Easter Sunday
    print("  Easter Sunday:")
    hymns = service.get_hymns(prima_domenica=False, domenica_festiva=True, tipo_festivita=FestivityType.PASQUA)
    sacramento_hymn = hymns[1]  # Second position should be Sacramento
    print(f"    Sacramento hymn: #{sacramento_hymn.number}: {sacramento_hymn.title}")
    print(f"    Category: {sacramento_hymn.category}")
    print(f"    Tags: {sacramento_hymn.tags}")
    
    # Check if it has inappropriate festive tags
    category_lower = sacramento_hymn.category.lower()
    if category_lower == 'natale':
        print("    ❌ FAILED: Sacramento hymn is from natale category in Easter Sunday")
    else:
        print("    ✅ PASSED: Sacramento hymn is not from inappropriate festive category")

if __name__ == "__main__":
    test_festive_filtering()
