"""Service for managing hymn selection history and avoiding repetition."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Set

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from database.database import db_manager
from database.models import HymnSelection, SelectedHymn, Ward
from hymns.models import FestivityType, Hymn
from hymns.service import HymnService
from utils.date_utils import get_next_sunday

logger = logging.getLogger(__name__)


class HymnHistoryService:
    """Service for managing hymn selection history and smart selection."""
    
    def __init__(self, hymn_service: HymnService):
        """Initialize the history service."""
        self.hymn_service = hymn_service
        self.lookback_weeks = 5  # Don't repeat hymns within 5 weeks
    
    def get_or_create_ward(self, ward_id: int = None, ward_name: str = None, session: Session = None) -> Ward:
        """Get ward by id or get/create by name."""
        ward = None
        if ward_id is not None:
            ward = session.query(Ward).filter(Ward.id == ward_id).first()
            return ward

        if ward_name:
            ward = session.query(Ward).filter(Ward.name == ward_name).first()
            if not ward:
                ward = Ward(name=ward_name)
                session.add(ward)
                session.flush()  # Get the ID
        return ward
    
    def get_recent_hymn_numbers(self, ward_id: int = None, ward_name: str = None, session: Session = None, weeks_back: Optional[int] = None) -> Set[int]:
        """Get hymn numbers used in the last N weeks for a ward."""
        if weeks_back is None:
            weeks_back = self.lookback_weeks
        
        cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
        
        # Get recent selections for this ward
        query = session.query(HymnSelection).join(Ward).filter(HymnSelection.selection_date >= cutoff_date)
        if ward_id is not None:
            query = query.filter(Ward.id == ward_id)
        elif ward_name:
            query = query.filter(Ward.name == ward_name)

        recent_selections = query.all()
        
        # Collect all hymn numbers from these selections
        used_hymns = set()
        for selection in recent_selections:
            for hymn in selection.hymns:
                used_hymns.add(hymn.hymn_number)
        
        logger.info(f"Found {len(used_hymns)} recently used hymns for ward '{ward_name}' in last {weeks_back} weeks")
        return used_hymns
    
    def filter_available_hymns(self, hymns: List[Hymn], used_hymns: Set[int]) -> List[Hymn]:
        """Filter out recently used hymns from available options."""
        available = [hymn for hymn in hymns if hymn.number not in used_hymns]
        logger.info(f"Filtered hymns: {len(hymns)} total -> {len(available)} available")
        return available
    
    def get_smart_hymns(
        self,
        ward_id: int = None,
        ward_name: str = None,
        prima_domenica: bool = False,
        domenica_festiva: bool = False,
        tipo_festivita: Optional[FestivityType] = None,
        selection_date: Optional[datetime] = None
    ) -> List[Hymn]:
        """
        Get hymns with smart selection to avoid recent repetition.
        
        Args:
            ward_name: Name of the ward
            prima_domenica: First Sunday of month (3 hymns instead of 4)
            domenica_festiva: Festive Sunday
            tipo_festivita: Type of festivity
            selection_date: Date of selection (defaults to now)
        
        Returns:
            List of selected hymns
        """
        if selection_date is None:
            selection_date = get_next_sunday()
        
        with db_manager.session_scope() as session:
            # Get recently used hymns (prefer id)
            used_hymns = self.get_recent_hymn_numbers(ward_id=ward_id, ward_name=ward_name, session=session)
            
            # Get all available hymns using the existing service
            hymn_count = 3 if prima_domenica else 4
            
            # Get Sacramento hymns (required for second position) with festive filtering
            sacramento_hymns = self.hymn_service._get_sacramento_hymns(domenica_festiva, tipo_festivita)
            available_sacramento = self.filter_available_hymns(sacramento_hymns, used_hymns)
            
            # If no Sacramento hymns are available, expand the lookback
            if not available_sacramento:
                logger.warning("No available Sacramento hymns, expanding lookback period")
                used_hymns = self.get_recent_hymn_numbers(ward_name=ward_name, session=session, weeks_back=3)
                available_sacramento = self.filter_available_hymns(sacramento_hymns, used_hymns)
                
                # If still no Sacramento hymns, use any Sacramento hymn (it's required)
                if not available_sacramento:
                    logger.warning("Still no Sacramento hymns available, using any Sacramento hymn")
                    available_sacramento = self.hymn_service._get_sacramento_hymns(domenica_festiva, tipo_festivita)
            
            # Get other hymns based on criteria
            other_hymns = self.hymn_service._get_other_hymns(domenica_festiva, tipo_festivita)
            available_other = self.filter_available_hymns(other_hymns, used_hymns)
            
            # Check if we have enough other hymns
            required_other_hymns = hymn_count - 1  # -1 for the Sacramento hymn
            if len(available_other) < required_other_hymns:
                logger.warning(f"Not enough other hymns available ({len(available_other)} < {required_other_hymns}), expanding lookback")
                used_hymns = self.get_recent_hymn_numbers(ward_name=ward_name, session=session, weeks_back=3)
                available_other = self.filter_available_hymns(other_hymns, used_hymns)
                
                # If still not enough, use original selection logic
                if len(available_other) < required_other_hymns:
                    logger.warning("Still not enough hymns, falling back to original selection")
                    return self.hymn_service.get_hymns(prima_domenica, domenica_festiva, tipo_festivita)
            
            # Select hymns using the smart filtering
            import random
            selected_other = random.sample(available_other, required_other_hymns)
            selected_sacramento = random.choice(available_sacramento)
            
            # Arrange hymns: first hymn, then sacramento, then the rest
            if hymn_count == 3:
                hymns_list = [selected_other[0], selected_sacramento, selected_other[1]]
            else:
                hymns_list = [selected_other[0], selected_sacramento] + selected_other[1:]
            
            logger.info(f"Selected {len(hymns_list)} hymns with smart filtering for ward '{ward_name or ward_id}'")
            return hymns_list
    
    def save_selection(
        self,
        hymns: List[Hymn],
        ward_id: int = None,
        ward_name: str = None,
        prima_domenica: bool = False,
        domenica_festiva: bool = False,
        tipo_festivita: Optional[FestivityType] = None,
        selection_date: Optional[datetime] = None
    ) -> HymnSelection:
        """
        Save a hymn selection to the database.
        
        Args:
            ward_name: Name of the ward
            hymns: List of selected hymns
            prima_domenica: First Sunday of month
            domenica_festiva: Festive Sunday
            tipo_festivita: Type of festivity
            selection_date: Date of selection (defaults to now)
        
        Returns:
            The saved HymnSelection object
        """
        if selection_date is None:
            selection_date = get_next_sunday()
        
        with db_manager.session_scope() as session:
            # Get or create ward (prefer id)
            ward = None
            if ward_id is not None:
                ward = session.query(Ward).filter(Ward.id == ward_id).first()
                if not ward:
                    raise ValueError(f"Ward id {ward_id} not found")
            else:
                ward = self.get_or_create_ward(ward_id=None, ward_name=ward_name, session=session)
            
            # Create selection record
            selection = HymnSelection(
                ward_id=ward.id,
                selection_date=selection_date,
                prima_domenica=prima_domenica,
                domenica_festiva=domenica_festiva,
                tipo_festivita=tipo_festivita.value if tipo_festivita else None
            )
            session.add(selection)
            session.flush()  # Get the ID
            
            # Create hymn records
            for position, hymn in enumerate(hymns, 1):
                selected_hymn = SelectedHymn(
                    selection_id=selection.id,
                    hymn_number=hymn.number,
                    hymn_title=hymn.title,
                    hymn_category=hymn.category,
                    position=position
                )
                session.add(selected_hymn)
            
            session.commit()
            logger.info(f"Saved hymn selection for ward '{ward.name if ward else ward_id}' with {len(hymns)} hymns")
            return selection
    
    def delete_selection(
        self,
        ward_id: int = None,
        ward_name: str = None,
        selection_date: datetime = None
    ) -> bool:
        """
        Delete a hymn selection from the database.
        
        Args:
            ward_name: Name of the ward
            selection_date: Date of the selection to delete
        
        Returns:
            True if deleted, False if not found
        """
        with db_manager.session_scope() as session:
            # Get ward by id or name
            ward = None
            if ward_id is not None:
                ward = session.query(Ward).filter(Ward.id == ward_id).first()
            elif ward_name:
                ward = session.query(Ward).filter(Ward.name == ward_name).first()
            if not ward:
                logger.warning(f"Ward '{ward_name}' not found")
                return False
            
            # Find the selection
            selection_date_only = selection_date.replace(hour=0, minute=0, second=0, microsecond=0)
            selection = (
                session.query(HymnSelection)
                .filter(
                    and_(
                        HymnSelection.ward_id == ward.id,
                        HymnSelection.selection_date >= selection_date_only,
                        HymnSelection.selection_date < selection_date_only + timedelta(days=1)
                    )
                )
                .first()
            )
            
            if not selection:
                logger.warning(f"Selection not found for ward '{ward_name}' on {selection_date}")
                return False
            
            # Delete associated hymns (cascade should handle this, but being explicit)
            for hymn in selection.hymns:
                session.delete(hymn)
            
            # Delete the selection
            session.delete(selection)
            session.commit()
            
            logger.info(f"Deleted hymn selection for ward '{ward.name if ward else ward_id}' on {selection_date}")
            return True
    
    def get_ward_history(self, ward_id: int = None, ward_name: str = None, limit: int = 10) -> List[dict]:
        """Get recent hymn selection history for a ward."""
        with db_manager.session_scope() as session:
            query = session.query(HymnSelection).join(Ward)
            if ward_id is not None:
                query = query.filter(Ward.id == ward_id)
            elif ward_name:
                query = query.filter(Ward.name == ward_name)

            query = query.order_by(desc(HymnSelection.selection_date)).limit(limit)
            selections = query.all()
            
            # Convert to dictionaries to avoid session issues
            result = []
            for selection in selections:
                hymns_data = []
                for hymn in sorted(selection.hymns, key=lambda h: h.position):
                    hymns_data.append({
                        'position': hymn.position,
                        'hymn_number': hymn.hymn_number,
                        'hymn_title': hymn.hymn_title,
                        'hymn_category': hymn.hymn_category
                    })
                
                result.append({
                    'selection_date': selection.selection_date,
                    'prima_domenica': selection.prima_domenica,
                    'domenica_festiva': selection.domenica_festiva,
                    'tipo_festivita': selection.tipo_festivita,
                    'hymns': hymns_data
                })
            
            return result
    
    def get_all_wards(self) -> List[dict]:
        """Get list of all ward names."""
        with db_manager.session_scope() as session:
            wards = session.query(Ward).order_by(Ward.name).all()
            return [{'id': w.id, 'name': w.name} for w in wards]
    
    def get_replacement_hymn(
        self,
        position: int,
        ward_id: int = None,
        ward_name: str = None,
        prima_domenica: bool = False,
        domenica_festiva: bool = False,
        tipo_festivita: Optional[FestivityType] = None,
        exclude_numbers: Optional[Set[int]] = None
    ) -> Hymn:
        """
        Get a random replacement hymn for a specific position.
        
        Args:
            position: Position of the hymn (1-4)
            ward_name: Name of the ward
            prima_domenica: First Sunday of month
            domenica_festiva: Festive Sunday
            tipo_festivita: Type of festivity
            exclude_numbers: Set of hymn numbers to exclude (current selection)
        
        Returns:
            A replacement hymn
        """
        import random
        
        if exclude_numbers is None:
            exclude_numbers = set()
        
        with db_manager.session_scope() as session:
            # Get recently used hymns (prefer id)
            used_hymns = self.get_recent_hymn_numbers(ward_id=ward_id, ward_name=ward_name, session=session)
            
            # Combine with explicitly excluded hymns
            all_excluded = used_hymns | exclude_numbers
            
            # Position 2 is always Sacramento
            if position == 2:
                available_hymns = self.hymn_service._get_sacramento_hymns(domenica_festiva, tipo_festivita)
            else:
                available_hymns = self.hymn_service._get_other_hymns(domenica_festiva, tipo_festivita)
            
            # Filter out excluded hymns
            available = [h for h in available_hymns if h.number not in all_excluded]
            
            # If no hymns available, expand the exclusion criteria
            if not available:
                available = [h for h in available_hymns if h.number not in exclude_numbers]
            
            if not available:
                raise ValueError(f"No available hymns for position {position}")
            
            return random.choice(available)
    
    def get_available_hymns(
        self,
        position: int,
        ward_id: int = None,
        ward_name: str = None,
        prima_domenica: bool = False,
        domenica_festiva: bool = False,
        tipo_festivita: Optional[FestivityType] = None,
        exclude_numbers: Optional[Set[int]] = None
    ) -> List[Hymn]:
        """
        Get all available hymns for a specific position.
        
        Args:
            position: Position of the hymn (1-4)
            ward_name: Name of the ward
            prima_domenica: First Sunday of month
            domenica_festiva: Festive Sunday
            tipo_festivita: Type of festivity
            exclude_numbers: Set of hymn numbers to exclude (current selection)
        
        Returns:
            List of available hymns sorted by number
        """
        if exclude_numbers is None:
            exclude_numbers = set()
        
        with db_manager.session_scope() as session:
            # Get recently used hymns (prefer id)
            used_hymns = self.get_recent_hymn_numbers(ward_id=ward_id, ward_name=ward_name, session=session)
            
            # Combine with explicitly excluded hymns
            all_excluded = used_hymns | exclude_numbers
            
            # Position 2 is always Sacramento
            if position == 2:
                available_hymns = self.hymn_service._get_sacramento_hymns(domenica_festiva, tipo_festivita)
            else:
                available_hymns = self.hymn_service._get_other_hymns(domenica_festiva, tipo_festivita)
            
            # Filter out excluded hymns
            available = [h for h in available_hymns if h.number not in all_excluded]
            
            # Sort by hymn number
            available.sort(key=lambda h: h.number)
            
            return available

    def update_hymn_in_selection(
        self,
        position: int,
        new_hymn: Hymn,
        ward_id: int = None,
        ward_name: str = None,
    ) -> bool:
        """
        Update a hymn in the most recent selection for a ward.
        
        Args:
            ward_name: Name of the ward
            position: Position of the hymn to update (1-4)
            new_hymn: The new hymn to set
        
        Returns:
            True if update was successful, False if no selection found
        """
        with db_manager.session_scope() as session:
            # Get the most recent selection for this ward
            query = (
                session.query(HymnSelection)
                .join(Ward)
                .order_by(desc(HymnSelection.selection_date))
            )
            if ward_id is not None:
                query = query.filter(Ward.id == ward_id)
            elif ward_name:
                query = query.filter(Ward.name == ward_name)

            most_recent = query.first()
            
            if not most_recent:
                logger.warning(f"No selection found for ward '{ward_name}' to update")
                return False
            
            # Find the hymn at the specified position
            hymn_to_update = None
            for selected_hymn in most_recent.hymns:
                if selected_hymn.position == position:
                    hymn_to_update = selected_hymn
                    break
            
            if not hymn_to_update:
                logger.warning(f"No hymn found at position {position} in selection")
                return False
            
            # Update the hymn
            old_number = hymn_to_update.hymn_number
            hymn_to_update.hymn_number = new_hymn.number
            hymn_to_update.hymn_title = new_hymn.title
            hymn_to_update.hymn_category = new_hymn.category
            
            # Touch the parent selection to update the updated_at timestamp
            most_recent.updated_at = datetime.utcnow()  # type: ignore
            
            session.commit()
            logger.info(f"Updated hymn at position {position} for ward '{ward_name or ward_id}': #{old_number} -> #{new_hymn.number}")
            return True
