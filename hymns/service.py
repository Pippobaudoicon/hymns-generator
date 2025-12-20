"""Service layer for hymn management and business logic."""

import json
import logging
import random
from pathlib import Path
from typing import List, Optional, Set

from .exceptions import DataLoadError, DataNotFoundError, InsufficientHymnsError, InvalidFilterError
from .models import FestivityType, Hymn, HymnFilter

logger = logging.getLogger(__name__)


class HymnService:
    """Service for managing hymns and implementing business logic."""

    def __init__(self, data_path: str):
        """Initialize the service with hymn data."""
        self.hymns: List[Hymn] = []
        self._load_hymns(data_path)
        logger.info(f"Loaded {len(self.hymns)} hymns from {data_path}")

    def _load_hymns(self, path: str) -> None:
        """Load hymns from JSON file."""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise DataLoadError(f"Data file not found: {path}")

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise DataLoadError("Invalid data format: expected list")

            # Process each hymn to extract audio URL and metadata
            processed_data = []
            for item in data:
                # Extract audio URL from assets
                audio_url = None
                if "assets" in item and len(item["assets"]) > 0:
                    media_obj = item["assets"][0].get("mediaObject", {})
                    if media_obj.get(
                        "assetType"
                    ) == "AUDIO_ACCOMPANIMENT" or media_obj.get("accompaniment"):
                        audio_url = media_obj.get("distributionUrl")

                # Extract composers and authors
                composers = [c.get("personName", "") for c in item.get("composers", [])]
                authors = [a.get("personName", "") for a in item.get("authors", [])]

                # Add extracted data to the item
                item["audio_url"] = audio_url
                item["composers"] = composers
                item["authors"] = authors

                processed_data.append(item)

            self.hymns = [Hymn.model_validate(item) for item in processed_data]

            if not self.hymns:
                raise DataLoadError("No hymns found in data file")

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise DataLoadError(f"Failed to load hymn data: {e}")

    def _filter_by_category(self, category: str) -> List[Hymn]:
        """Filter hymns by category."""
        return [h for h in self.hymns if h.category.lower() == category.lower()]

    def _filter_by_tags(self, tag: str) -> List[Hymn]:
        """Filter hymns by tag."""
        return [h for h in self.hymns if tag.lower() in [t.lower() for t in h.tags]]

    def _exclude_special_occasions(self, hymns: List[Hymn]) -> List[Hymn]:
        """Exclude special occasion hymns."""
        return [h for h in hymns if h.category.lower() != "occasioni speciali"]

    def _exclude_festive_hymns(
        self, hymns: List[Hymn], allowed_festivity: Optional[str] = None
    ) -> List[Hymn]:
        """
        Exclude festive hymns (Christmas and Easter) unless specifically allowed.

        Args:
            hymns: List of hymns to filter
            allowed_festivity: If specified, hymns with this festive category or tag will be included

        Returns:
            Filtered list of hymns
        """

        def should_exclude_hymn(hymn: Hymn) -> bool:
            category_lower = hymn.category.lower()
            tags_lower = [tag.lower() for tag in hymn.tags]

            # Always exclude hymns from festive categories
            if category_lower == "natale":
                return allowed_festivity != "natale"

            if category_lower == "pasqua":
                return allowed_festivity != "pasqua"

            # Only exclude by tags if we have a specific festivity requirement
            # (i.e., on festive Sundays, exclude hymns with wrong festive tags)
            if allowed_festivity is not None:
                # On festive Sundays, exclude hymns with inappropriate festive tags
                if "natale" in tags_lower and allowed_festivity != "natale":
                    return True
                if "pasqua" in tags_lower and allowed_festivity != "pasqua":
                    return True

            # Non-festive hymn or no specific festivity requirement - don't exclude
            return False

        return [h for h in hymns if not should_exclude_hymn(h)]

    def _get_sacramento_hymns(
        self,
        domenica_festiva: bool = False,
        tipo_festivita: Optional[FestivityType] = None,
    ) -> List[Hymn]:
        """Get all Sacramento category hymns, applying festive filtering."""
        sacramento_hymns = self._filter_by_category("sacramento")

        # Apply strict festive filtering (now includes both category and tag filtering)
        if domenica_festiva and tipo_festivita:
            # Allow only the specified festivity type
            sacramento_hymns = self._exclude_festive_hymns(
                sacramento_hymns, tipo_festivita.value
            )
        else:
            # Exclude all festive hymns when not a festive Sunday
            sacramento_hymns = self._exclude_festive_hymns(sacramento_hymns, None)

        return sacramento_hymns

    def _get_other_hymns(
        self, domenica_festiva: bool, tipo_festivita: Optional[FestivityType]
    ) -> List[Hymn]:
        """Get hymns that are not Sacramento based on criteria."""
        # Start with all non-Sacramento hymns
        other_hymns = [h for h in self.hymns if h.category.lower() != "sacramento"]

        if domenica_festiva:
            if not tipo_festivita:
                raise InvalidFilterError(
                    "tipo_festivita is required when domenica_festiva is true"
                )

            # Start with festive hymns by category
            festive_hymns_by_category = self._filter_by_category(tipo_festivita.value)
            festive_hymns_by_category = [
                h
                for h in festive_hymns_by_category
                if h.category.lower() != "sacramento"
            ]

            # Add festive hymns by tags (from other categories)
            festive_hymns_by_tags = self._filter_by_tags(tipo_festivita.value)
            festive_hymns_by_tags = [
                h
                for h in festive_hymns_by_tags
                if h.category.lower() != "sacramento"
                and h.category.lower() != tipo_festivita.value
            ]

            # Combine festive hymns and remove duplicates first
            festive_hymns = festive_hymns_by_category + festive_hymns_by_tags

            # Remove duplicates (in case a hymn appears in multiple lists)
            seen_numbers = set()
            unique_festive_hymns = []
            for hymn in festive_hymns:
                if (
                    hymn.number not in seen_numbers
                    and hymn.category.lower() != "sacramento"
                ):
                    unique_festive_hymns.append(hymn)
                    seen_numbers.add(hymn.number)

            # Apply strict festive filtering - only allow the specified festivity type
            other_hymns = self._exclude_festive_hymns(
                unique_festive_hymns, tipo_festivita.value
            )

            # If still not enough hymns, add only the needed amount from "occasioni speciali"
            required_hymns = 3  # Assuming worst case of 4 total - 1 Sacramento
            if len(other_hymns) < required_hymns:
                hymns_needed = required_hymns - len(other_hymns)
                logger.warning(
                    f"Only {len(other_hymns)} festive hymns available, adding {hymns_needed} from occasioni speciali"
                )
                special_occasion_hymns = self._filter_by_category("occasioni speciali")
                # Add only the exact number of occasioni speciali needed
                added_count = 0
                for hymn in special_occasion_hymns:
                    if hymn.number not in seen_numbers and added_count < hymns_needed:
                        # Only exclude if it has conflicting festive tags
                        tags_lower = [tag.lower() for tag in hymn.tags]
                        has_conflicting_tags = False
                        if tipo_festivita.value == "natale" and "pasqua" in tags_lower:
                            has_conflicting_tags = True
                        elif (
                            tipo_festivita.value == "pasqua" and "natale" in tags_lower
                        ):
                            has_conflicting_tags = True

                        if not has_conflicting_tags:
                            other_hymns.append(hymn)
                            seen_numbers.add(hymn.number)
                            added_count += 1
        else:
            # Exclude special occasions and all festive hymns (strict enforcement)
            other_hymns = self._exclude_special_occasions(other_hymns)
            other_hymns = self._exclude_festive_hymns(other_hymns, None)

        return other_hymns

    def get_hymns(
        self,
        prima_domenica: bool = False,
        domenica_festiva: bool = False,
        tipo_festivita: Optional[FestivityType] = None,
    ) -> List[Hymn]:
        """
        Generate a list of hymns according to the rules:
        - 3 hymns for first Sunday, 4 otherwise
        - Second hymn must be from Sacramento category
        - Special handling for festive Sundays
        """
        try:
            hymn_count = 3 if prima_domenica else 4

            # Get Sacramento hymns (required for second position) with festive filtering
            sacramento_hymns = self._get_sacramento_hymns(
                domenica_festiva, tipo_festivita
            )
            if not sacramento_hymns:
                raise InsufficientHymnsError("No Sacramento hymns available")

            # Get other hymns based on criteria
            other_hymns = self._get_other_hymns(domenica_festiva, tipo_festivita)

            # Check if we have enough hymns
            required_other_hymns = hymn_count - 1  # -1 for the Sacramento hymn
            if len(other_hymns) < required_other_hymns:
                raise InsufficientHymnsError(
                    f"Need {required_other_hymns} non-Sacramento hymns, but only {len(other_hymns)} available"
                )

            # Select hymns
            selected_other = random.sample(other_hymns, required_other_hymns)
            selected_sacramento = random.choice(sacramento_hymns)

            # Arrange hymns: first hymn, then sacramento, then the rest
            if hymn_count == 3:
                hymns_list = [selected_other[0], selected_sacramento, selected_other[1]]
            else:
                hymns_list = [selected_other[0], selected_sacramento] + selected_other[
                    1:
                ]

            logger.info(f"Selected {len(hymns_list)} hymns for service")
            return hymns_list

        except Exception as e:
            if isinstance(e, (InvalidFilterError, InsufficientHymnsError)):
                raise
            logger.error(f"Error generating hymns: {e}")
            raise InsufficientHymnsError("Failed to generate hymns")

    def get_hymn(self, hymn_filter: HymnFilter) -> Optional[Hymn]:
        """
        Get a single hymn based on filter criteria.
        All criteria are applied with AND logic.
        """
        try:
            filtered_hymns = self.hymns.copy()

            # Apply filters
            if hymn_filter.number is not None:
                filtered_hymns = [
                    h for h in filtered_hymns if h.number == hymn_filter.number
                ]

            if hymn_filter.category is not None:
                filtered_hymns = [
                    h
                    for h in filtered_hymns
                    if h.category.lower() == hymn_filter.category.lower()
                ]

            if hymn_filter.tag is not None:
                filtered_hymns = [
                    h
                    for h in filtered_hymns
                    if hymn_filter.tag.lower() in [t.lower() for t in h.tags]
                ]

            if not filtered_hymns:
                return None

            # Return random hymn from filtered results
            selected_hymn = random.choice(filtered_hymns)
            logger.info(
                f"Selected hymn: {selected_hymn.title} (#{selected_hymn.number})"
            )
            return selected_hymn

        except Exception as e:
            logger.error(f"Error filtering hymns: {e}")
            raise DataNotFoundError("Failed to retrieve hymn")

    def get_hymn_by_number(self, number: int) -> Optional[Hymn]:
        """Get a specific hymn by its number."""
        for hymn in self.hymns:
            if hymn.number == number:
                return hymn
        return None

    def get_categories(self) -> List[str]:
        """Get all available hymn categories."""
        categories = {hymn.category for hymn in self.hymns}
        return sorted(list(categories))

    def get_tags(self) -> List[str]:
        """Get all available hymn tags."""
        tags: Set[str] = set()
        for hymn in self.hymns:
            tags.update(hymn.tags)
        return sorted(list(tags))

    def get_stats(self) -> dict:
        """Get statistics about the hymn collection."""
        return {
            "total_hymns": len(self.hymns),
            "categories": len(self.get_categories()),
            "tags": len(self.get_tags()),
            "sacramento_hymns": len(self._get_sacramento_hymns()),
        }
