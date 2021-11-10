"""AMP model."""
import functools

from .. import _TORCHMNMC


class autocast:
    """We do not leverage PyTorch AMP because the list of supported ops is different."""

    # pylint: disable=missing-docstring

    def __init__(self, enabled=True):
        self._enabled = enabled

    def __enter__(self):
        _TORCHMNMC._mnm_set_amp_enabled(self._enabled)

    def __exit__(self, *args):
        _TORCHMNMC._mnm_set_amp_enabled(False)
        return False

    def __call__(self, func):
        @functools.wraps(func)
        def decorate_autocast(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return decorate_autocast
