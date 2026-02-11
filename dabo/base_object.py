# -*- coding: utf-8 -*-
import string
import types

from . import settings
from .constants import NULL_NAME
from .event_mixin import EventMixin
from .lib.propertyHelperMixin import PropertyHelperMixin
from .localization import _

NONE_TYPE = type(None)


class dObject(PropertyHelperMixin, EventMixin):
    """The basic ancestor of all Dabo objects."""

    # Local attributes
    _baseClass = None
    _basePrefKey = ""
    _logEvents = None
    _name = NULL_NAME
    _parent = None
    _preferenceManager = None
    _properties = None

    # Subclasses can set these to False, in which case they are responsible
    # for maintaining the following call order:
    #   self._beforeInit()
    #   # optional stuff
    #   super().__init__()
    #   # optional stuff
    #   self._afterInit()
    # or, not calling super() at all, but remember to call _initProperties() and
    # the call to setProperties() at the end!
    _call_beforeInit, _call_afterInit, _call_initProperties = True, True, True

    def __init__(self, properties=None, attProperties=None, *args, **kwargs):
        if self._call_beforeInit:
            self._beforeInit()
        if self._call_initProperties:
            self._initProperties()

        # Now that user code has had an opportunity to set the properties, we can
        # see if there are properties sent to the constructor which will augment
        # or override the properties set in beforeInit().

        # Some classes that are not inherited from the ui-layer PEM mixin classes
        # can have attProperties passed. Since these are all passed as strings, we
        # need to convert them to their proper type and add them to the properties
        # dict.
        if properties is None:
            properties = {}
        if attProperties:
            for prop, val in list(attProperties.items()):
                if prop in ("designerClass",):
                    continue
                if prop in properties:
                    # The properties value has precedence, so ignore.
                    continue
                typ = type(getattr(self, prop))
                if not issubclass(typ, str):
                    if issubclass(typ, bool):
                        val = val == "True"
                    elif typ is NONE_TYPE:
                        val = None
                    else:
                        try:
                            val = typ(val)
                        except ValueError as e:
                            # Sometimes int values can be stored as floats
                            if typ in (int, int):
                                val = float(val)
                            else:
                                raise e
                properties[prop] = val

        # The keyword properties can come from either, both, or none of:
        #    + the properties dict
        #    + the kwargs dict
        # Get them sanitized into one dict:
        if properties is not None:
            # Override the class values
            for k, v in list(properties.items()):
                self._properties[k] = v
        properties = self._extractKeywordProperties(kwargs, self._properties)
        if kwargs:
            # Some kwargs haven't been handled.
            bad = ", ".join(["'%s'" % kk for kk in kwargs])
            raise TypeError("Invalid keyword arguments passed to %s: %s" % (self.__repr__(), bad))

        if self._call_afterInit:
            self._afterInit()
        self.setProperties(properties)

        super().__init__()

    def __repr__(self):
        bc = self.BaseClass
        if bc is None:
            bc = self.__class__
        strval = "%s" % bc
        classname = strval.split("'")[1]
        classparts = classname.split(".")
        if ".ui.ui" in classname:
            # Simplify the different UI toolkits
            pos = classparts.index("ui")
            classparts.pop(pos + 1)
        # Remove the duplicate class name that happens
        # when the class name is the same as the file.
        while (len(classparts) > 1) and (classparts[-1] == classparts[-2]):
            classparts.pop()
        classname = ".".join(classparts)

        try:
            nm = self.Name
        except AttributeError:
            nm = ""

        regid = getattr(self, "RegID", "")
        if regid:
            nm = regid

        if (not nm) or (nm == NULL_NAME):
            # No name; use module.classname
            nm = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        if not self:
            print("I'm dead")
        _id = self._getID()
        return "<%(nm)s (baseclass %(classname)s, id:%(_id)s)>" % locals()

    def _getID(self):
        """
        Defaults to the Python id() function. Objects in sub-modules, such as the various
        UI toolkits, can override to substitute something more relevant to them.
        """
        return id(self)

    def beforeInit(self, *args, **kwargs):
        """
        Subclass hook. Called before the object is fully instantiated.
        Usually, user code should override afterInit() instead, but there may be
        cases where you need to set an attribute before the init stage is fully
        underway.
        """
        pass

    def afterInit(self):
        """
        Subclass hook. Called after the object's __init__ has run fully.
        Subclasses should place their __init__ code here in this hook, instead of
        overriding __init__ directly, to avoid conflicting with base Dabo behavior.
        """
        pass

    def initProperties(self):
        """
        Hook for subclasses. User subclasses should set properties
        here, such as::

            self.Name = "MyTextBox"
            self.BackColor = (192,192,192)

        """
        pass

    def initEvents(self):
        """
        Hook for subclasses. User code should do custom event binding
        here, such as::

            self.bindEvent(events.GotFocus, self.customGotFocusHandler)

        """
        pass

    def _beforeInit(self):
        """Framework subclass hook."""
        self.beforeInit()

    def _initProperties(self):
        """Framework subclass hook."""
        self.initProperties()

    def _afterInit(self):
        """Framework subclass hook."""
        self.afterInit()

    def getAbsoluteName(self):
        """Return the fully qualified name of the object."""
        names = [self.Name]
        obj = self
        while True:
            try:
                parent = obj.Parent
            except AttributeError:
                # Parent not necessarily defined
                parent = None
            if parent:
                try:
                    name = parent.Name
                except AttributeError:
                    name = NULL_NAME
                names.append(name)
                obj = parent
            else:
                break
        names.reverse()
        return ".".join(names)

    def getMethodList(cls, refresh=False):
        """Return the list of (Dabo) methods for this class or instance."""
        try:
            methodList = cls.__methodList
        except AttributeError:
            methodList = None

        if refresh:
            methodList = None

        if isinstance(methodList, list):
            ## A prior call has already generated the methodList
            return methodList

        methodList = []
        for c in cls.__mro__:
            for item in dir(c):
                if item[0] in string.lowercase:
                    if item in c.__dict__:
                        if type(c.__dict__[item]) in (types.MethodType, types.FunctionType):
                            if methodList.count(item) == 0:
                                methodList.append(item)
        methodList.sort()
        cls.__methodList = methodList
        return methodList

    getMethodList = classmethod(getMethodList)

    def _addCodeAsMethod(self, cd):
        """
        This method takes a dictionary containing method names as
        keys, and the method code as the corresponding values, compiles
        it, and adds the methods to this object. If the method name begins
        with 'on', and autoBindEvents is True, an event binding will be
        made just as with normal auto-binding. If the code cannot be
        compiled successfully, an error message will be added
        to the Dabo ErrorLog, and the method will not be added.
        """
        for nm, code in list(cd.items()):
            try:
                code = code.replace("\n]", "]")
                compCode = compile(code, "", "exec")
            except SyntaxError as e:
                snm = self.Name
                log.error(
                    _("Method '%(nm)s' of object '%(snm)s' has the following error: %(e)s")
                    % locals()
                )
                continue
            # OK, we have the compiled code. Add it to the class definition.
            # NOTE: if the method name and the name in the 'def' statement
            # are not the same, the results are undefined, and will probably crash.
            nmSpace = {}
            exec(compCode, nmSpace)
            mthd = nmSpace[nm]
            exec("self.%s = %s.__get__(self)" % (nm, nm))
            newMethod = types.MethodType(mthd, self)
            setattr(self, nm, newMethod)

    # Property definitions begin here
    @property
    def Application(self):
        """Read-only object reference to the Dabo Application object.  (dApp)."""
        return settings.get_application()

    @property
    def BaseClass(self):
        """The base Dabo class of the object. Read-only  (type)

        Every Dabo baseclass must set self._baseClass explicitly, to itself. For instance:
            class dBackend(object):
               def __init__(self):
                   self._baseClass = dBackend
        In other words, BaseClass isn't the actual Python base class of the object, but the
        Dabo-relative base class.
        """
        try:
            return self._baseClass
        except AttributeError:
            return None

    @property
    def BasePrefKey(self):
        """Base key used when saving/restoring preferences  (str)"""
        return self._basePrefKey

    @BasePrefKey.setter
    def BasePrefKey(self, val):
        if not isinstance(val, (str,)):
            raise TypeError("BasePrefKey must be a string.")
        self._basePrefKey = val
        pm = self.PreferenceManager
        if pm is not None:
            if not pm._key:
                pm._key = val

    @property
    def Class(self):
        """The class the object is based on. Read-only.  (class)"""
        return self.__class__

    @property
    def LogEvents(self):
        """
        Specifies which events to log.  (list of strings)

        If the first element is 'All', all events except the following listed events will be logged.
        Event logging is resource-intensive, so in addition to setting this LogEvents property, you
        also need to make the following call:

            >>> settings.eventLogging = True

        This is expensive, as it is semi-recursive upwards in the containership until some parent
        object finally reports a LogEvents property. In normal use, this will be the Application
        object.
        """
        if self._logEvents is None:
            # Try to get the value from the parent object, or the Application if
            # no Parent.
            if self.Parent is not None:
                parent = self.Parent
            else:
                if self == self.Application:
                    parent = None
                else:
                    parent = self.Application
            try:
                le = parent.LogEvents
            except AttributeError:
                le = []
            self._logEvents = le
        return self._logEvents

    @LogEvents.setter
    def LogEvents(self, val):
        self._logEvents = list(val)

    @property
    def Name(self):
        """The name of the object.  (str)"""
        return self._name

    @Name.setter
    def Name(self, val):
        if not isinstance(val, (str,)):
            raise TypeError("Name must be a string.")
        if not len(val.split()) == 1:
            raise KeyError("Name must not contain any spaces")
        self._name = val

    @property
    def Parent(self):
        """The containing object.  (obj)

        Subclasses must override as necessary. Parent/child relationships don't exist for all
        nonvisual objects, and implementation of parent/child relationships will vary. This
        implementation is the simplest.
        """
        return self._parent

    @Parent.setter
    def Parent(self, obj):
        # Subclasses must override as necessary.
        self._parent = obj

    @property
    def PreferenceManager(self):
        if self._preferenceManager is None:
            if self.Application is not self:
                try:
                    self._preferenceManager = self.Application.PreferenceManager
                except AttributeError:
                    pass
            if self._preferenceManager is None:
                from .preference_mgr import dPref  ## here to avoid circular import

                self._preferenceManager = dPref(key=self.BasePrefKey)
        return self._preferenceManager

    @PreferenceManager.setter
    def PreferenceManager(self, val):
        """Reference to the Preference Management object  (dPref)"""
        from .preference_mgr import dPref  ## here to avoid circular import

        if not isinstance(val, dPref):
            raise TypeError("PreferenceManager must be a dPref object")
        self._preferenceManager = val


if __name__ == "__main__":
    from .application import dApp

    d = dObject()
    print(d.Application)
    app = dApp()
    print(d.Application)
