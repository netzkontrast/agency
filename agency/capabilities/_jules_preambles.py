"""Spec 060 back-compat shim — canonical module is `jules/preambles.py`."""
from .jules.preambles import *  # noqa: F401, F403
from .jules.preambles import (  # noqa: F401
    DISPATCH_SELF_SOURCE,
    REVIEW_COMMENT_TAIL,
    _MUST_NAME_TOOLS,
    assemble,
    lint_must_name,
    review_comment,
)
