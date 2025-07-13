"""Test the fallback logic for occasioni speciali hymns."""

import pytest
from unittest.mock import MagicMock
from hymns.service import HymnService
from hymns.models import FestivityType


class TestFallbackLogic:
    """Test fallback to occasioni speciali hymns."""

    def test_occasioni_speciali_only_fills_remaining_slots(self):
        """Test that occasioni speciali are only added to fill the remaining slots needed."""
        service = HymnService(data_path="data/italian_hymns_full.json")
        
        # Mock the data to have minimal pasqua hymns and some occasioni speciali
        original_hymns = service.hymns.copy()
        
        # Create test data: 2 pasqua hymns (need 3 total, so should add only 1 occasioni)
        test_hymns = [
            # Sacramento hymn
            MagicMock(number=1, category="sacramento", tags=[]),
            # 2 Pasqua hymns
            MagicMock(number=2, category="pasqua", tags=["pasqua"]),
            MagicMock(number=3, category="pasqua", tags=["pasqua"]),
            # 3 Occasioni speciali hymns (should only take 1)
            MagicMock(number=4, category="occasioni speciali", tags=[]),
            MagicMock(number=5, category="occasioni speciali", tags=[]),
            MagicMock(number=6, category="occasioni speciali", tags=[]),
            # Some normal hymns
            MagicMock(number=7, category="apertura", tags=[]),
            MagicMock(number=8, category="chiusura", tags=[]),
        ]
        
        service.hymns = test_hymns
        
        try:
            result = service.get_hymns(
                prima_domenica=False,
                domenica_festiva=True,
                tipo_festivita=FestivityType.PASQUA
            )
            
            # Should have 4 hymns total
            assert len(result) == 4
            
            # Should have 1 sacramento hymn
            sacramento_hymns = [h for h in result if h.category == "sacramento"]
            assert len(sacramento_hymns) == 1
            
            # Should have 2 pasqua hymns (all available)
            pasqua_hymns = [h for h in result if h.category == "pasqua"]
            assert len(pasqua_hymns) == 2
            
            # Should have exactly 1 occasioni speciali hymn (to fill the gap)
            occasioni_hymns = [h for h in result if h.category == "occasioni speciali"]
            assert len(occasioni_hymns) == 1
            
            print(f"Total hymns: {len(result)}")
            print(f"Sacramento: {len(sacramento_hymns)}")
            print(f"Pasqua: {len(pasqua_hymns)}")
            print(f"Occasioni speciali: {len(occasioni_hymns)}")
            
        finally:
            # Restore original hymns
            service.hymns = original_hymns

    def test_no_occasioni_speciali_when_enough_festive_hymns(self):
        """Test that no occasioni speciali are added when enough festive hymns exist."""
        service = HymnService(data_path="data/italian_hymns_full.json")
        
        # Mock the data to have enough pasqua hymns
        original_hymns = service.hymns.copy()
        
        # Create test data: 5 pasqua hymns (more than needed)
        test_hymns = [
            # Sacramento hymn
            MagicMock(number=1, category="sacramento", tags=[]),
            # 5 Pasqua hymns (more than the 3 needed)
            MagicMock(number=2, category="pasqua", tags=["pasqua"]),
            MagicMock(number=3, category="pasqua", tags=["pasqua"]),
            MagicMock(number=4, category="pasqua", tags=["pasqua"]),
            MagicMock(number=5, category="pasqua", tags=["pasqua"]),
            MagicMock(number=6, category="pasqua", tags=["pasqua"]),
            # Some occasioni speciali hymns (should not be selected)
            MagicMock(number=7, category="occasioni speciali", tags=[]),
            MagicMock(number=8, category="occasioni speciali", tags=[]),
        ]
        
        service.hymns = test_hymns
        
        try:
            result = service.get_hymns(
                prima_domenica=False,
                domenica_festiva=True,
                tipo_festivita=FestivityType.PASQUA
            )
            
            # Should have 4 hymns total
            assert len(result) == 4
            
            # Should have 1 sacramento hymn
            sacramento_hymns = [h for h in result if h.category == "sacramento"]
            assert len(sacramento_hymns) == 1
            
            # Should have 3 pasqua hymns
            pasqua_hymns = [h for h in result if h.category == "pasqua"]
            assert len(pasqua_hymns) == 3
            
            # Should have 0 occasioni speciali hymns (not needed)
            occasioni_hymns = [h for h in result if h.category == "occasioni speciali"]
            assert len(occasioni_hymns) == 0
            
        finally:
            # Restore original hymns
            service.hymns = original_hymns

    def test_exact_count_with_mixed_sources(self):
        """Test that we get exactly the right count from mixed sources."""
        service = HymnService(data_path="data/italian_hymns_full.json")
        
        original_hymns = service.hymns.copy()
        
        # Create test data: 1 pasqua category + 1 pasqua tag + 1 occasioni (= 3 total needed)
        test_hymns = [
            # Sacramento hymn
            MagicMock(number=1, category="sacramento", tags=[]),
            # 1 Pasqua category hymn
            MagicMock(number=2, category="pasqua", tags=["pasqua"]),
            # 1 hymn with pasqua tag but different category
            MagicMock(number=3, category="apertura", tags=["pasqua"]),
            # 2 Occasioni speciali hymns (should only take 1)
            MagicMock(number=4, category="occasioni speciali", tags=[]),
            MagicMock(number=5, category="occasioni speciali", tags=[]),
        ]
        
        service.hymns = test_hymns
        
        try:
            result = service.get_hymns(
                prima_domenica=False,
                domenica_festiva=True,
                tipo_festivita=FestivityType.PASQUA
            )
            
            # Should have 4 hymns total
            assert len(result) == 4
            
            # Should have 1 sacramento hymn
            sacramento_hymns = [h for h in result if h.category == "sacramento"]
            assert len(sacramento_hymns) == 1
            
            # Should have exactly 3 other hymns
            other_hymns = [h for h in result if h.category != "sacramento"]
            assert len(other_hymns) == 3
            
            # Should include the pasqua category hymn
            pasqua_category_hymns = [h for h in result if h.category == "pasqua"]
            assert len(pasqua_category_hymns) == 1
            
            # Should include the hymn with pasqua tag
            pasqua_tag_hymns = [h for h in result if "pasqua" in h.tags and h.category != "pasqua"]
            assert len(pasqua_tag_hymns) == 1
            
            # Should include exactly 1 occasioni speciali hymn
            occasioni_hymns = [h for h in result if h.category == "occasioni speciali"]
            assert len(occasioni_hymns) == 1
            
        finally:
            # Restore original hymns
            service.hymns = original_hymns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
