"""Utility for processing timer settings from POST."""


def _parse_int(val, default, min_val=None, max_val=None):
    try:
        n = int(float(val))
        if min_val is not None and n < min_val:
            n = min_val
        if max_val is not None and n > max_val:
            n = max_val
        return n
    except (TypeError, ValueError):
        return default


def process_timer_settings(request):
    """
    Process timer settings from POST. Call when action=='settings'.
    Returns (timer_enabled, timer_seconds) and saves to session.
    """
    timer_enabled = request.POST.get('timer_enabled') == 'on'
    timer_seconds = _parse_int(request.POST.get('timer_seconds'), 3, 1, 60)
    request.session['timer_enabled'] = timer_enabled
    request.session['timer_seconds'] = timer_seconds
    return timer_enabled, timer_seconds
