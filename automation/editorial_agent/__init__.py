"""Editorial automation for verbovivo.blog."""

# Quarterly rollout compatibility hook. It only corrects metadata parsing and
# can be removed once the fix is folded directly into lessons.py.
from . import lessons as _lessons
from .quarterly_compat import install as _install_quarterly_compat
from .lesson_product_links import install as _install_lesson_product_links

_install_quarterly_compat(_lessons)
_install_lesson_product_links(_lessons)
