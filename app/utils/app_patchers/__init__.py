# flake8: noqa: F401

import app.utils.app_patchers.i18n as _
import app.utils.app_patchers.json_logger as _
from app.utils.app_patchers.base import Patcher

__all__ = ("patch",)

patch = Patcher.patch
