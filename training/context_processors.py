"""Context processors for global template variables."""


def timer(request):
    """Add timer_enabled and timer_seconds to context (global, default off)."""
    return {
        'timer_enabled': request.session.get('timer_enabled', False),
        'timer_seconds': request.session.get('timer_seconds', 3),
    }
