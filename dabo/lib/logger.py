# -*- coding: utf-8 -*-
import os
import sys
import time

from dabo.dLocalize import _
from dabo.dObject import dObject
from dabo.lib.utils import ustr


class Log(dObject):
    """Generic logger object for Dabo.

    The main dabo module will instantiate singleton instances of this, which
    custom code can override to redirect the writing of informational and error
    messages.

    So, to display general informational messages, call:
        dabo.log.info("message")

    For error messages, call:
        dabo.log.error("message")

    By default, infoLog writes to stdout and errorLog to stderr. But your code
    can redirect these messages however you please. Just set the LogObject property
    to an instance that has a write() method that will receive and act on the
    message. For example, you can redirect to a file:

        dabo.errorLog.LogObject = open("/tmp/error.log", "w")
        dabo.infoLog.LogObject = open("/dev/null", "w")

    You can set the logs to arbitrary objects. As long as the object has a write()
    method that receives a message parameter, it will work.
    """

    def write(self, message):
        """Writes the passed message to the log."""
        if self.LogObject is None:
            # Send messages to the bit bucket...
            return
        msg = []
        if self.Caption:
            msg.append("%s: " % self.Caption)
        if self.LogTimeStamp:
            msg.append("%s: " % time.asctime())
        msg.append(message)
        msg.append(os.linesep)
        msg = "".join(msg)
        try:
            self.LogObject.write(msg)
        except UnicodeEncodeError:
            self.LogObject.write(msg.encode("utf-8"))
        except UnicodeDecodeError:
            try:
                self.LogObject.write(msg.decode("utf-8"))
            except UnicodeDecodeError:
                self.LogObject.write(msg.decode("latin-1"))
        # Flush the log entry to the file
        try:
            self.LogObject.flush()
        except (AttributeError, IOError):
            pass

    @property
    def Caption(self):
        """The log's label: will get prepended to the log entry"""
        try:
            return self._caption
        except AttributeError:
            return ""

    @Caption.setter
    def Caption(self, val):
        self._caption = ustr(val)

    @property
    def LogObject(self):
        """The object that is to receive the log messages."""
        try:
            return self._logObject
        except AttributeError:
            return sys.stdout

    @LogObject.setter
    def LogObject(self, logObject):
        # assume that logObject is an object with a write() method...
        self._logObject = logObject

    @property
    def LogTimeStamp(self):
        """Specifies whether a timestamp is logged with the message. Default: True"""
        try:
            return self._logTimeStamp
        except AttributeError:
            return True

    @LogTimeStamp.setter
    def LogTimeStamp(self, val):
        self._logTimeStamp = bool(val)
