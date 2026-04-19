"""
hooks/registry.py — Hook registry. Add new hooks here.

To add a hook:
1. Create the class file in hooks/
2. Import it here
3. Add it to HOOKS dict

Everything else is automatic.
"""

from hooks.seo_rankings import SEORankingsHook
from hooks.pagespeed import PageSpeedHook

# Remaining hooks: stubs until implemented
# from hooks.reviews import ReviewsHook
# from hooks.ad_spend import AdSpendHook
# from hooks.social_presence import SocialPresenceHook
# from hooks.citations import CitationsHook
# from hooks.tech_stack import TechStackHook
# from hooks.ecommerce_traffic import EcommerceTrafficHook

HOOKS = {
    "seo_rankings": SEORankingsHook,
    "pagespeed": PageSpeedHook,
    # "reviews":            ReviewsHook,
    # "ad_spend":           AdSpendHook,
    # "social_presence":    SocialPresenceHook,
    # "citations":          CitationsHook,
    # "tech_stack":         TechStackHook,
    # "ecommerce_traffic":  EcommerceTrafficHook,
}


def get_hook(name: str):
    """Return instantiated hook by name. Raises KeyError if not found."""
    cls = HOOKS[name]
    return cls()


def list_hooks():
    return list(HOOKS.keys())
