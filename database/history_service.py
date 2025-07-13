"""Service for managing hymn selection history and avoiding repetition."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from database.models import Ward, HymnSelection, SelectedHymn
from database.database import db_manager
from hymns.models import Hymn, FestivityType
from hymns.service import HymnService

logger = logging.getLogger(__name__)


class HymnHistoryService:
    """Service for managing hymn selection history and smart selection."""
    
    def __init__(self, hymn_service: HymnService):
        """Initialize the history service."""
        self.hymn_service = hymn_service
        self.lookback_weeks = 5  # Don't repeat hymns within 5 weeks
    
    def get_or_create_ward(self, ward_name: str, session: Session) -> Ward:
        """Get or create a ward by name."""
        ward = session.query(Ward).filter(Ward.name == ward_name).first()
        if not ward:
            ward = Ward(name=ward_name)
            session.add(ward)
            session.flush()  # Get the ID
        return ward
    
    def get_recent_hymn_numbers(self, ward_name: str, session: Session, weeks_back: int = None) -> Set[int]:
        """Get hymn numbers used in the last N weeks for a ward."""
        if weeks_back is None:
            weeks_back = self.lookback_weeks
        
        cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
        
        # Get recent selections for this ward
        recent_selections = (
            session.query(HymnSelection)
            .join(Ward)
            .filter(
                and_(
                    Ward.name == ward_name,
                    HymnSelection.selection_date >= cutoff_date
                )
            )
            .all()
        )
        
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
        ward_name: str,
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
            selection_date = datetime.now()
        
        with db_manager.session_scope() as session:
            # Get recently used hymns
            used_hymns = self.get_recent_hymn_numbers(ward_name, session)
            
            # Get all available hymns using the existing service
            hymn_count = 3 if prima_domenica else 4
            
            # Get Sacramento hymns (required for second position) with festive filtering
            sacramento_hymns = self.hymn_service._get_sacramento_hymns(domenica_festiva, tipo_festivita)
            available_sacramento = self.filter_available_hymns(sacramento_hymns, used_hymns)
            
            # If no Sacramento hymns are available, expand the lookback
            if not available_sacramento:
                logger.warning("No available Sacramento hymns, expanding lookback period")
                used_hymns = self.get_recent_hymn_numbers(ward_name, session, weeks_back=3)
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
                used_hymns = self.get_recent_hymn_numbers(ward_name, session, weeks_back=3)
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
            
            logger.info(f"Selected {len(hymns_list)} hymns with smart filtering for ward '{ward_name}'")
            return hymns_list
    
    def save_selection(
        self,
        ward_name: str,
        hymns: List[Hymn],
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
            selection_date = datetime.now()
        
        with db_manager.session_scope() as session:
            # Get or create ward
            ward = self.get_or_create_ward(ward_name, session)
            
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
            logger.info(f"Saved hymn selection for ward '{ward_name}' with {len(hymns)} hymns")
            return selection
    
    def get_ward_history(self, ward_name: str, limit: int = 10) -> List[dict]:
        """Get recent hymn selection history for a ward."""
        with db_manager.session_scope() as session:
            selections = (
                session.query(HymnSelection)
                .join(Ward)
                .filter(Ward.name == ward_name)
                .order_by(desc(HymnSelection.selection_date))
                .limit(limit)
                .all()
            )
            
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
    
    def get_all_wards(self) -> List[str]:
        """Get list of all ward names."""
        with db_manager.session_scope() as session:
            wards = session.query(Ward.name).all()
            return [ward.name for ward in wards]
