# -*- coding: utf-8 -*-
import random
from pathlib import Path

from .. import settings
from ..base_object import dObject
from ..lib.connParser import importConnections
from ..lib.encryption import Encryption
from ..lib.xmltodict import xmltodict
from ..localization import _

dabo_module = settings.get_dabo_package()


class dConnectInfo(dObject):
    """
    Holder for the properties for connecting to the backend. Each
    backend may have different names for properties, but this object
    tries to abstract that. The value stored in the Password must be
    encrypted in the format set in the app. This class has  'encrypt' and
    'decrypt' functions for doing this, or you can set the PlainTextPassword
    property, and the class will encypt that value and set the Password
    property for you.

    You can create it in several ways, like most Dabo objects. First, you
    can pass all the settings as parameters to the constructor::

        ci = dConnectInfo(DbType="MySQL", Host="domain.com",
            User="daboUser", PlainTextPassword="secret", Port=3306,
            Database="myData", Name="mainConnection")

    Or you can create a dictionary of the various props, and pass that
    in the 'connInfo' parameter::

        connDict = {"DbType" : "MySQL", "Host" : "domain.com",
            "User" : "daboUser", "PlainTextPassword" : "secret",
            "Port" : 3306, "Database" : "myData", "Name" : "mainConnection"}
        ci = dConnectInfo(connInfo=connDict)

    Or you can create the object and then set the props
    individually::

        ci = dConnectInfo()
        ci.DbType = "MySQL"
        ci.Host = "domain.com"
        ci.User = "daboUser"
        ci.PlainTextPassword = "secret"
        ci.Database = "myData"
        ci.Name = "mainConnection"

    If you are running a remote app, should set the RemoteHost property instead of Host. The
    DbType will be "web".
    """

    def __init__(self, connInfo=None, **kwargs):
        self._baseClass = dConnectInfo
        self._backendObject = None
        self._host = self._user = self._password = self._dbType = self._database = self._port = (
            self._name
        ) = self._remoteHost = ""
        self._keepAliveInterval = None
        super().__init__(**kwargs)

        # Necessary when using this class outside of a Dabo application. See the docstring
        # for the dabo.application.Application.CryptoKey property for the format needed.
        self._encryption = Encryption()
        self._encryption.set_key(kwargs.get("crypto_key"))

        if connInfo:
            self.setConnInfo(connInfo)

    def setConnInfo(self, connInfo, nm=""):
        # Run through the connDict, and set the appropriate properties. If it isn't
        # a valid property name, raise TypeError.
        self._customParameters = {}
        props = [
            "Name",
            "DbType",
            "Host",
            "User",
            "Password",
            "Database",
            "PlainTextPassword",
            "Port",
            "RemoteHost",
            "KeepAliveInterval",
        ]
        lprops = [p.lower() for p in props]
        if isinstance(connInfo, (str, Path)) and Path(connInfo).exists():
            # See if it's a .cnxml file
            if isinstance(connInfo, Path):
                connInfo = connInfo.as_posix()
            connDict = importConnections(connInfo)
            # The dict has the connection name as the key, and the various settings as its value
            info = list(connDict.values())[0]
            self.Name = info.get("name", "")
            self.DbType = info.get("dbtype", "")
            self.Host = info.get("host", "")
            self.RemoteHost = info.get("remotehost", "")
            self.Database = info.get("database", "")
            self.User = info.get("user", "")
            self.Password = info.get("password", "")
            self.Port = info.get("port", "")
            self.KeepAliveInterval = info.get("KeepAliveInterval", "")
            return

        for k, v in list(connInfo.items()):
            try:
                propidx = lprops.index(k.lower())
            except ValueError:
                propidx = None
            if propidx is not None:
                setattr(self, props[propidx], v)
            else:
                self._customParameters[k] = v

    def getConnection(self, **kwargs):
        kwargs.update(self.CustomParameters)
        return self._backendObject.getConnection(self, **kwargs)

    def getDictCursorClass(self):
        try:
            return self._backendObject.getDictCursorClass()
        except TypeError:
            return None

    def getMainCursorClass(self):
        try:
            return self._backendObject.getMainCursorClass()
        except TypeError:
            return None

    def encrypt(self, val):
        if self.Application:
            return self.Application.encrypt(val)
        else:
            return self._encryption.encrypt(val)

    def decrypt(self, val):
        if self.Application:
            return self.Application.decrypt(val)
        else:
            return self._encryption.decrypt(val)

    def revealPW(self):
        return self.decrypt(self.Password)

    def getBackendObject(self):
        return self._backendObject

    @property
    def CustomParameters(self):
        """Additional parameters passed to backend object connect method. (dict)"""
        try:
            return self._customParameters.copy()
        except AttributeError:
            return {}

    @property
    def DbType(self):
        """Name of the backend database type.  (str)"""
        try:
            return self._dbType
        except AttributeError:
            return None

    @DbType.setter
    def DbType(self, dbType):
        """Set the backend type for the connection if valid."""
        _oldObject = self._backendObject
        # As other backends are coded into the framework, we will need
        # to expand the if/elif list.
        if dbType is not None:
            # Evaluate each type of backend
            nm = dbType.lower()
            try:
                if nm == "mysql":
                    from . import db_mysql

                    self._backendObject = db_mysql.MySQL()
                elif nm == "sqlite":
                    from . import db_sqlite

                    self._backendObject = db_sqlite.SQLite()
                elif nm == "firebird":
                    from . import db_firebird

                    self._backendObject = db_firebird.Firebird()
                elif nm == "postgresql":
                    from . import db_postgresql

                    self._backendObject = db_postgresql.Postgres()
                elif nm == "mssql":
                    from . import db_mssql

                    self._backendObject = db_mssql.MSSQL()
                elif nm == "oracle":
                    from . import db_oracle

                    self._backendObject = db_oracle.Oracle()
                elif nm == "web":
                    from . import db_web

                    self._backendObject = db_web.Web()
                elif nm == "odbc":
                    import dbODBC

                    self._backendObject = dbODBC.ODBC()
                else:
                    raise ValueError(f"Invalid database type: {nm}")
            except ImportError:
                dabo_module.log.error(
                    _(f"You do not have the database module for {dbType} installed")
                )
                self._dbType = None
                self._backendObject = None
            if _oldObject != self._backendObject:
                self._dbType = dbType
        else:
            self._dbType = None
            self._backendObject = None

    @property
    def Database(self):
        """The database name to login to. (str)"""
        return self._database

    @Database.setter
    def Database(self, database):
        self._database = database

    @property
    def Host(self):
        """The host name or ip address. (str)"""
        return self._host

    @Host.setter
    def Host(self, host):
        self._host = host

    @property
    def KeepAliveInterval(self):
        """
        Specifies how often a KeepAlive query should be sent to the server. (int)

        Defaults to None, meaning we never send a KeepAlive query. The interval
        is expressed in seconds.
        """
        return self._keepAliveInterval

    @KeepAliveInterval.setter
    def KeepAliveInterval(self, val):
        if not val:
            val = None
        else:
            val = int(val)
        self._keepAliveInterval = val

    @property
    def Name(self):
        """The name used to reference this connection. (str)"""
        return self._name

    @Name.setter
    def Name(self, val):
        self._name = val

    @property
    def Password(self):
        """The encrypted password of the user. (str)"""
        return self._password

    @Password.setter
    def Password(self, password):
        self._password = password

    @property
    def PlainTextPassword(self):
        """
        Write-only property that encrypts the value and stores that in the Password
        property. (str)
        """
        raise AttributeError("PlainTextPassword property is write-only")

    @PlainTextPassword.setter
    def PlainTextPassword(self, val):
        self._password = self.encrypt(val)

    @property
    def Port(self):
        """The port to connect on (may not be applicable for all databases). (int)"""
        return self._port

    @Port.setter
    def Port(self, port):
        try:
            self._port = int(port)
        except ValueError:
            self._port = None

    @property
    def RemoteHost(self):
        """When running as a web app, this holds the host URL. (str)"""
        return self._remoteHost

    @RemoteHost.setter
    def RemoteHost(self, host):
        self._remoteHost = host

    @property
    def User(self):
        """The user name. (str)"""
        return self._user

    @User.setter
    def User(self, user):
        self._user = user


if __name__ == "__main__":
    test = dConnectInfo()
    print(test.DbType)
    test.DbType = "MySQL"
    print(test.DbType)
    test.DbType = "SQLite"
    print(test.DbType)
