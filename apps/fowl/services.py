"""
Bloodline calculation service.
Handles auto-computation of bloodline percentages based on parentage.
"""
from decimal import Decimal
from collections import defaultdict
from typing import Dict, Optional
from .models import Gamefowl, FowlBloodline, Bloodline


def calculate_bloodline_percentages(
    fowl: Gamefowl,
    depth: int = 5,
    _cache: Optional[Dict] = None
) -> Dict[int, Decimal]:
    """
    Auto-calculate bloodline percentages based on parentage.

    Algorithm:
    1. If fowl has manually set bloodlines (is_manual_override=True), use those.
    2. If fowl has no parents but has bloodlines, use those (founding bird).
    3. Otherwise, inherit 50% from sire's bloodlines + 50% from dam's bloodlines.
    4. Recursively trace up to `depth` generations.

    Args:
        fowl: The Gamefowl instance to calculate percentages for.
        depth: Maximum generations to trace back (default 5).
        _cache: Internal cache for memoization.

    Returns:
        Dict mapping bloodline_id to percentage (as Decimal).
    """
    if _cache is None:
        _cache = {}

    # Check cache first
    cache_key = (fowl.pk, depth)
    if cache_key in _cache:
        return _cache[cache_key]

    # Check for manual override - these take absolute precedence
    manual_bloodlines = fowl.bloodline_percentages.filter(is_manual_override=True)
    if manual_bloodlines.exists():
        result = {bl.bloodline_id: bl.percentage for bl in manual_bloodlines}
        _cache[cache_key] = result
        return result

    # Base case: no parents -> return existing bloodlines (founding bird)
    if not fowl.sire and not fowl.dam:
        result = {
            bl.bloodline_id: bl.percentage
            for bl in fowl.bloodline_percentages.all()
        }
        _cache[cache_key] = result
        return result

    # Recursive case: calculate from parents
    bloodlines = defaultdict(Decimal)

    # Get sire bloodlines (contributes 50%)
    if fowl.sire and depth > 0:
        sire_bloodlines = calculate_bloodline_percentages(
            fowl.sire, depth - 1, _cache
        )
        for bl_id, pct in sire_bloodlines.items():
            bloodlines[bl_id] += pct * Decimal('0.5')

    # Get dam bloodlines (contributes 50%)
    if fowl.dam and depth > 0:
        dam_bloodlines = calculate_bloodline_percentages(
            fowl.dam, depth - 1, _cache
        )
        for bl_id, pct in dam_bloodlines.items():
            bloodlines[bl_id] += pct * Decimal('0.5')

    result = dict(bloodlines)
    _cache[cache_key] = result
    return result


def save_calculated_bloodlines(fowl: Gamefowl, force_recalculate: bool = False) -> None:
    """
    Calculate and persist bloodline percentages for a fowl.

    Args:
        fowl: The Gamefowl instance.
        force_recalculate: If True, clears ALL existing bloodlines first.
                          If False, only clears auto-calculated ones.
    """
    if force_recalculate:
        fowl.bloodline_percentages.all().delete()
    else:
        # Only clear auto-calculated entries, keep manual overrides
        fowl.bloodline_percentages.filter(is_manual_override=False).delete()

    percentages = calculate_bloodline_percentages(fowl)

    # Save new calculations
    for bloodline_id, percentage in percentages.items():
        if percentage > 0:
            # Check if manual override exists for this bloodline
            existing = fowl.bloodline_percentages.filter(
                bloodline_id=bloodline_id,
                is_manual_override=True
            ).first()

            if not existing:
                FowlBloodline.objects.create(
                    fowl=fowl,
                    bloodline_id=bloodline_id,
                    percentage=percentage,
                    is_manual_override=False
                )


def propagate_bloodlines_to_offspring(fowl: Gamefowl) -> int:
    """
    Recalculate bloodlines for all descendants when a parent's bloodlines change.

    Args:
        fowl: The parent fowl whose bloodlines changed.

    Returns:
        Number of descendants updated.
    """
    updated_count = 0
    descendants = fowl.get_descendants(generations=10)  # Deep propagation

    for desc_info in descendants:
        desc_fowl = desc_info['fowl']
        # Only recalculate if the fowl doesn't have ALL manual overrides
        has_auto = desc_fowl.bloodline_percentages.filter(
            is_manual_override=False
        ).exists()
        has_no_manual = not desc_fowl.bloodline_percentages.filter(
            is_manual_override=True
        ).exists()

        if has_auto or has_no_manual:
            save_calculated_bloodlines(desc_fowl)
            updated_count += 1

    return updated_count


def get_bloodline_breakdown(fowl: Gamefowl) -> dict:
    """
    Get a detailed bloodline breakdown for display.

    Returns a dict with:
    - 'percentages': List of (bloodline_name, percentage, is_manual)
    - 'total': Sum of all percentages (should be ~100)
    - 'is_complete': Whether percentages sum to 100
    """
    bloodlines = fowl.bloodline_percentages.select_related('bloodline').all()

    percentages = [
        {
            'name': bl.bloodline.name,
            'percentage': float(bl.percentage),
            'is_manual': bl.is_manual_override,
            'bloodline_id': bl.bloodline_id,
        }
        for bl in bloodlines
    ]

    total = sum(p['percentage'] for p in percentages)

    return {
        'percentages': percentages,
        'total': total,
        'is_complete': 99.5 <= total <= 100.5,  # Allow small rounding errors
    }


def set_manual_bloodlines(
    fowl: Gamefowl,
    bloodline_percentages: Dict[int, Decimal]
) -> None:
    """
    Set manual bloodline percentages for a fowl.
    This will override auto-calculation.

    Args:
        fowl: The Gamefowl instance.
        bloodline_percentages: Dict mapping bloodline_id to percentage.
    """
    # Clear existing bloodlines
    fowl.bloodline_percentages.all().delete()

    # Create new manual entries
    for bloodline_id, percentage in bloodline_percentages.items():
        if percentage > 0:
            FowlBloodline.objects.create(
                fowl=fowl,
                bloodline_id=bloodline_id,
                percentage=percentage,
                is_manual_override=True
            )


def get_common_bloodlines(fowl1: Gamefowl, fowl2: Gamefowl) -> list:
    """
    Get bloodlines that two fowl have in common.
    Useful for breeding compatibility analysis.

    Returns list of dicts with bloodline info and combined percentages.
    """
    bl1 = {bl.bloodline_id: bl for bl in fowl1.bloodline_percentages.all()}
    bl2 = {bl.bloodline_id: bl for bl in fowl2.bloodline_percentages.all()}

    common_ids = set(bl1.keys()) & set(bl2.keys())

    common = []
    for bl_id in common_ids:
        common.append({
            'bloodline': bl1[bl_id].bloodline,
            'fowl1_percentage': bl1[bl_id].percentage,
            'fowl2_percentage': bl2[bl_id].percentage,
            'avg_percentage': (bl1[bl_id].percentage + bl2[bl_id].percentage) / 2,
        })

    return sorted(common, key=lambda x: x['avg_percentage'], reverse=True)
