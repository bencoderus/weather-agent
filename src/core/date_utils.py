from datetime import datetime, timedelta
import re

def get_current_date() -> str:
    return datetime.utcnow().date().isoformat()

def normalize_date(date_str: str = '') -> str:
    """Converts natural date phrases (e.g. 'tomorrow', 'two days time') into 'YYYY-MM-DD'."""
    today = datetime.utcnow().date()
    
    if not date_str or date_str.lower() == 'today':
        return today.isoformat()

    text = date_str.strip().lower()

    if text in ['tomorrow']:
        return (today + timedelta(days=1)).isoformat()
    if text in ['next tomorrow', 'the day after tomorrow']:
        return (today + timedelta(days=2)).isoformat()

    match = re.match(r'(\d+)\s+days?\s*time', text)
    if match:
        days = int(match.group(1))
        if days > 5:
            raise ValueError("Forecast is limited to 5 days ahead.")
        return (today + timedelta(days=days)).isoformat()

    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    if text in weekdays:
        today_idx = today.weekday()
        target_idx = weekdays.index(text)
        delta = (target_idx - today_idx) % 7
        if delta > 5:
            raise ValueError("Forecast is limited to 5 days ahead.")
        return (today + timedelta(days=delta)).isoformat()

    try:
        return datetime.strptime(text, '%Y-%m-%d').date().isoformat()
    except ValueError:
        raise ValueError(f"Unsupported date format: {date_str}")
