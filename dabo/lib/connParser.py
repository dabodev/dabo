# -*- coding: utf-8 -*-
import os.path
import sys
import xml.sax
from io import StringIO

from .. import application
from .. import settings
from ..localization import _
from . import utils

# Tuple containing all file-based database types.
FILE_DATABASES = ("sqlite",)


class connHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.connDict = {}
        self.blankConn = {
            "name": "",
            "dbtype": "",
            "host": "",
            "remotehost": "",
            "database": "",
            "user": "",
            "password": "",
            "port": "",
            "KeepAliveInterval": "",
        }
        self.currDict = self.blankConn.copy()
        self.element = None

    def startElement(self, name, attrs):
        self.element = name
        if name == "connection":
            for att in list(attrs.keys()):
                if att == "dbtype":
                    dbType = attrs.getValue("dbtype").split(":")
                    self.currDict["dbtype"] = dbType[0]
                    if len(dbType) > 1:
                        self.currDict["driver"] = dbType[1]
        self.attributes = attrs

    def characters(self, content):
        if self.element and self.element not in ("connectiondefs", "connection"):
            if self.element in self.currDict:
                self.currDict[self.element] += content
            else:
                # We can now define custom connection parameters, example:
                # <dialect type="int">1</dialect>
                # It's an extended connection information, we log it.
                elem = self.element
                dabo.log.info(
                    _("Extended database connection parameter loaded: %(elem)s = %(content)s")
                    % locals()
                )
                atype = self.attributes.get("type", None)
                if not atype:
                    # Set default type to 'str'.
                    atype = "str"
                self.currDict[self.element] = globals()["__builtins__"][atype](content)

    def endElement(self, name):
        if name == "connection":
            if self.currDict:
                # Save it to the conn dict
                nm = self.currDict["name"]
                if not nm:
                    # name not defined: follow the old convention of user@host
                    nm = self.currDict["name"] = "%s@%s" % (
                        self.currDict["user"],
                        self.currDict["host"],
                    )
                self.connDict[nm] = self.currDict.copy()
                self.currDict = self.blankConn.copy()
        self.element = None
        self.attributes = None

    def getConnectionDict(self):
        return self.connDict


def importConnections(pth=None, useHomeDir=False):
    """Read the connection info in the file passed as 'pth', and return
    a dict containing connection names as keys and connection info
    dicts as the values.

    If 'useHomeDir' is True, any file-based database connections
    will have their pathing resolved based upon the app's current
    HomeDirectory. Otherwise, the path will be resolved relative to
    the connection file itself.
    """
    if pth is None:
        return None
    ch = connHandler()
    with open(pth) as ff:
        xml.sax.parse(ff, ch)
    ret = ch.getConnectionDict()
    basePath = pth
    if useHomeDir:
        basePath = settings.get_application().HomeDirectory
    else:
        basePath = pth

    for cxn, data in list(ret.items()):
        dbtype = data.get("dbtype", "")
        if dbtype.lower() in FILE_DATABASES:
            for key, val in list(data.items()):
                if key == "database":
                    osp = os.path
                    relpath = utils.resolvePath(val, basePath, abspath=False)
                    abspath = osp.abspath(osp.join(osp.split(basePath)[0], relpath))
                    if osp.exists(abspath):
                        ret[cxn][key] = abspath
    return ret


def createXML(cxns, encoding=None):
    """Returns the XML for the passed connection info. The info
    can either be a single dict of connection info, or a list/tuple of
    such dicts.
    """
    ret = getXMLWrapper(encoding=encoding)
    cxml = ""
    if isinstance(cxns, (list, tuple)):
        for cx in cxns:
            cxml += genConnXML(cx)
    else:
        cxml = genConnXML(cxns)
    return ret % cxml


def genConnXML(d):
    """Receive a dict containing connection info, and return
    a 'connection' XML element.
    """
    from dabo.lib.xmltodict import escQuote

    try:
        if "name" not in d:
            if not d["user"]:
                d["user"] = "anybody"
            if not d["host"]:
                d["host"] = "local"
            d["name"] = "%s@%s" % (d["user"], d["host"])
        ret = getConnTemplate() % (
            escQuote(d["dbtype"], noQuote=True),
            escQuote(d["name"], noQuote=True),
            escQuote(d["host"], noQuote=True),
            escQuote(d["database"], noQuote=True),
            escQuote(d["user"], noQuote=True),
            escQuote(d["password"], noQuote=True),
            d["port"],
        )
    except KeyError:
        # Not a valid conn info dict
        ret = ""
    return ret
    ### pkm: I'm pretty sure we want to remove the above try block and propagate
    ###      the exceptions instead of returning "", but am leaving it as-is for
    ###      now for lack of time to test the repercussions.


def fileRef(ref=""):
    """Handles the passing of file names, file objects, or raw XML to the
    parser. Returns an open file-like object, or None. It is up to the calling
    program to close the file.
    """
    ret = None
    if isinstance(ref, str):
        if os.path.exists(ref):
            return open(ref)
        else:
            return StringIO(ref)


def getXMLWrapper(encoding=None):
    if encoding is None:
        encoding = dabo.getXMLEncoding()
    return """<?xml version="1.0" encoding="%s" standalone="yes"?>
<connectiondefs xmlns="http://www.dabodev.com"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.dabodev.com conn.xsd"
xsi:noNamespaceSchemaLocation = "http://dabodev.com/schema/conn.xsd">

%s

</connectiondefs>
""" % (
        encoding,
        "%s",
    )


def getConnTemplate():
    return """    <connection dbtype="%s">
        <name>%s</name>
        <host>%s</host>
        <database>%s</database>
        <user>%s</user>
        <password>%s</password>
        <port>%s</port>
    </connection>
"""
