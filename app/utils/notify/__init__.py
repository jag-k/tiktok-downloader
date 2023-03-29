# flake8: noqa: F401

from app.utils.notify.base import *
import app.utils.notify.chanify as _
import app.utils.notify.file_reporter as _

send_message = Notify.init().send_message
