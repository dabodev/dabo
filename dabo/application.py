# -*- coding: utf-8 -*-
import configparser
import datetime
import glob
import importlib
import inspect
import json
import locale
import logging
import logging.handlers
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import warnings
from io import StringIO
from pathlib import Path
from xml.sax._exceptions import SAXParseException
from zipfile import ZipFile

from . import db
from . import exceptions
from . import lib
from . import localization
from . import settings
from . import ui
from . import user_setting_provider
from .base_object import dObject
from .lib import connParser
from .lib.encryption import Encryption
from .lib.utils import cleanMenuCaption
from .lib.utils import ustr
from .localization import _
from .preference_mgr import dPref
from .security_manager import dSecurityManager

dabo_module = settings.get_dabo_package()


class Collection(list):
    """Collection : Base class for the various collection
    classes used in the app object.
    """

    def __init__(self):
        list.__init__(self)

    def add(self, objRef):
        """Add the object reference to the collection."""
        self.append(objRef)

    def remove(self, objRef):
        """Delete the object reference from the collection."""
        try:
            index = self.index(objRef)
        except ValueError:
            index = None
        if index is not None:
            del self[index]


class TempFileHolder(object):
    """Utility class to get temporary file names and to make sure they are
    deleted when the Python session ends.
    """

    def __init__(self):
        self._tempFiles = []

    def __del__(self):
        self._eraseTempFiles()

    def _eraseTempFiles(self):
        # Try to erase all temp files created during life.
        # Need to re-import the os module here for some reason.
        try:
            import os

            for f in self._tempFiles:
                if not os.path.exists(f):
                    continue
                try:
                    os.remove(f)
                except OSError as e:
                    if not f.endswith(".pyc"):
                        # Don't worry about the .pyc files, since they may not be there
                        print("Could not delete %s: %s" % (f, e))
        except Exception as e:
            # In these rare cases, Python has already 'gone away', so just bail
            pass

    def release(self):
        self._eraseTempFiles()

    def append(self, f):
        self._tempFiles.append(f)

    def getTempFile(self, ext=None, badChars=None, directory=None):
        if ext is None:
            ext = "py"
        if badChars is None:
            badChars = "-:"
        fname = ""
        suffix = ".%s" % ext
        while not fname:
            if directory is None:
                fd, tmpname = tempfile.mkstemp(suffix=suffix)
            else:
                fd, tmpname = tempfile.mkstemp(suffix=suffix, dir=directory)
            os.close(fd)
            bad = [ch for ch in badChars if ch in os.path.split(tmpname)[1]]
            if not bad:
                fname = tmpname
        self.append(fname)
        if fname.endswith(".py"):
            # Track the .pyc file, too.
            self.append(fname + "c")
        return fname


class dApp(dObject):
    """
    The containing object for the entire application.

    All Dabo objects have an Application property which refers to the dApp
    instance. Instantiate your dApp object from your main script, like so::

    >>> from application import dApp
    >>> app = dApp()
    >>> app.start()

    Normally, dApp gets instantiated from the client app's main Python script,
    and lives through the life of the application.

        -- Set up an empty data connections dict that contains connection objects
        -- that use descriptive names as their keys. Obviously this requires that
        -- each connection has a unique name; if you create connections with
        -- identical names, the second one read in will overwrite the first, and
        -- the results are not guaranteed. Once read in, the only identifier for a
        -- connection is its name; the file from which it was read in, if any, is
        -- irrelevant. Any .cnxml files found in the app home directory, the
        -- current directory (if different) or any subdirectory named 'db' or
        -- 'data' of the home/current directory will be automatically read into the
        -- connections dict, but the connections aren't made until requested by the
        -- app. Additionally, connections defined in Python code in a file named
        -- 'dbConnectionDefs.py' will be imported. This is an old behavior that
        -- should no longer be used.

        -- Set up a DB Connection manager, that is basically a dictionary
        -- of dConnection objects. This allows connections to be shared
        -- application-wide.

        -- look for a MainForm in an expected place, otherwise use default dabo
        -- dFormMain, and instantiate that.

        -- maintain a forms collection and provide interfaces for
        -- opening dForms, closing them, and iterating through them.

        -- start the main app event loop.

        -- clean up and exit gracefully

    """

    _call_beforeInit, _call_afterInit, _call_initProperties = False, False, True
    # Behaviors which are normal in the framework may need to
    # be modified when run as the Designer. This flag will
    # distinguish between the two states.
    isDesigner = False

    def __init__(self, selfStart=False, ignoreScriptDir=False, properties=None, *args, **kwargs):
        # Some apps, such as the visual tools, are meant to be run from directories
        # other than that where they are located. In those cases, use the current dir.
        self._ignoreScriptDir = ignoreScriptDir

        self._uiAlreadySet = False
        self._beforeInit()

        # If we are displaying a splash screen, these attributes control
        # its appearance. Extract them before the super call.
        self.showSplashScreen = self._extractKey(kwargs, "showSplashScreen", False)
        basepath = settings.root_path
        img = os.path.join(basepath, "icons", "daboSplashName.png")
        self.splashImage = self._extractKey(kwargs, "splashImage", img)
        self.splashMaskColor = self._extractKey(kwargs, "splashMaskColor", None)
        self.splashTimeout = self._extractKey(kwargs, "splashTimeout", 5000)

        super().__init__(properties, *args, **kwargs)
        # egl: added the option of keeping the main form hidden
        # initially. The default behavior is for it to be shown, as usual.
        self.showMainFormOnStart = True
        self._wasSetup = False
        # Track names of menus whose MRUs need to be persisted. Set
        # the key for each entry to the menu caption, and the value to
        # the bound function.
        self._persistentMRUs = {}
        # Create the temp file handlers.
        self._tempFileHolder = TempFileHolder()
        self.getTempFile = self._tempFileHolder.getTempFile
        # Create the framework-level preference manager
        self._frameworkPrefs = dPref(key="dabo_framework")
        # Hold a reference to the bizobj and connection, if any, controlling
        # the current database transaction
        self._transactionTokens = {}
        # Holds update check times in case of errors.
        self._lastCheckInfo = None
        # Reference to the Encryption object
        self._encryption = Encryption()
        # Location and Name of the project; used for Web Update
        self._projectInfo = (None, None)
        self._setProjInfo()
        # Other Web Update values
        self.projectAbbrevs = {
            "dabo": "frm",
            "class designer": "cds",
            "cxn editor": "cxe",
            "editor": "edt",
            "menu designer": "mds",
            "preference editor": "prf",
            "report designer": "rds",
            "wizards": "wiz",
            "dabodemo": "dem",
        }
        self.webUpdateDirs = {
            "dabo": "dabo",
            "class designer": "ide",
            "cxn editor": "ide",
            "editor": "ide",
            "menu designer": "ide",
            "preference editor": "ide",
            "report designer": "ide",
            "wizards": "ide",
            "dabodemo": "demo",
        }

        # List of form classes to open on App Startup
        self._formsToOpen = []
        # Form to open if no forms were passed as a parameter
        self._defaultForm = None
        # Dict of "Last-Modified" values for dynamic web resources
        self._sourceLastModified = {}

        # For simple UI apps, this allows the app object to be created
        # and started in one step. It also suppresses the display of
        # the main form.
        if selfStart:
            self.showMainFormOnStart = False
            self.setup()

        # If running as a web app, sync the files
        rp = self._RemoteProxy
        if rp:
            try:
                rp.syncFiles()
            except urllib.error.URLError as e:
                code, msg = e.reason
                if code == 61:
                    # Connection refused; server's down
                    print(
                        _(
                            """


The connection was refused by the server. Most likely this means that
the server is not running. Please have that problem corrected, and
try again when it is running.

"""
                        )
                    )
                    sys.exit(61)

        self._afterInit()
        self.autoBindEvents()

        # Set this instance as the main application object
        dabo_module.app_reference = self

    def resyncFiles(self):
        """
        In the middle of an app's lifetime, files on the remote server may
        have been updated. This will ensure that the local copy is in sync.
        """
        rp = self._RemoteProxy
        if rp:
            try:
                rp.syncFiles()
            except urllib.error.URLError as e:
                # Cannot sync; record the error and move on
                dabo_module.error(_("File re-sync failed. Reason: %s") % e)

    def __del__(self):
        """Make sure that temp files are removed"""
        self._tempFileHolder.release()

    def setup(self, initUI=True):
        """Set up the application object."""
        # dabo is going to want to import various things from the Home Directory
        if self.HomeDirectory not in sys.path:
            sys.path.append(self.HomeDirectory)

        def initAppInfo(item, default):
            if not self.getAppInfo(item):
                self.setAppInfo(item, default)

        initAppInfo("appName", "Dabo Application")
        initAppInfo("appShortName", self.getAppInfo("appName").replace(" ", ""))
        initAppInfo("appVersion", "")
        initAppInfo("vendorName", "")

        # If there's a locale directory for the app and it looks valid, install it:
        localeDir = os.path.join(self.HomeDirectory, "locale")
        localeDomain = self.getAppInfo("appShortName").replace(" ", "_").lower()
        if os.path.isdir(localeDir) and localization.isValidDomain(localeDomain, localeDir):
            lang = getattr(self, "_language", None)
            charset = getattr(self, "_charset", None)
            localization.install(localeDomain, localeDir)
            localization.setLanguage(lang, charset)

        # Add the 'lib' directory, if present, to sys.path
        libdir = os.path.join(self.HomeDirectory, "lib")
        sys.path.append(libdir)
        # Initialize the Dabo modules into the app namespace
        self._initModuleNames()
        self._initDB()

        if initUI:
            if self.showSplashScreen:
                self.uiApp = ui.getUiApp(
                    self, uiAppClass=None, callback=self.initUIApp, forceNew=True
                )
            else:
                self.uiApp = ui.uiApp(self, callback=None)
            self.initUIApp()
        else:
            self.uiApp = None

        # Flip the flag
        self._wasSetup = True
        # Call the afterSetup hook
        self.afterSetup()

    def afterSetup(self):
        """
        Hook method that is called after the app's setup code has run, and the
        database, UI and module references have all been established.
        """
        pass

    def startupForms(self):
        """
        Open one or more of the defined forms. The default one is specified
        in self.DefaultForm. If form names were passed on the command line,
        they will be opened instead of the default one as long as they exist.
        """
        form_names = [class_name[3:] for class_name in dir(self.ui) if class_name[:3] == "Frm"]
        for arg in sys.argv[1:]:
            arg = arg.lower()
            for form_name in form_names:
                if arg == form_name.lower():
                    self.FormsToOpen.append(getattr(self.ui, "Frm%s" % form_name))
        if not self.FormsToOpen and self.DefaultForm:
            self.FormsToOpen.append(self.DefaultForm)
        for frm in self.FormsToOpen:
            frm(self.MainForm).show()

    def initUIApp(self):
        """
        Callback from the initial app setup. Used to allow the
        splash screen, if any, to be shown quickly.
        """
        self.uiApp.setup()

    def start(self):
        """Start the application event loop."""
        if not self._wasSetup:
            # Convenience; if you don't need to customize setup(), just
            # call start()
            self.setup()

        self._finished = False
        if (
            not self.SecurityManager
            or not self.SecurityManager.RequireAppLogin
            or getattr(self, "_loggedIn", False)
            or self.SecurityManager.login()
        ):
            ui.callAfterInterval(5000, self._destroySplash)
            self._retrieveMRUs()
            try:
                self._loginDialog.Parent = None
                self._loginDialog.release()
                del self._loginDialog
            except AttributeError:
                pass
            self.uiApp.start()
        if not self._finished:
            self.finish()

    def finish(self):
        """
        Called when the application event loop has ended. You may also
        call this explicitly to exit the application event loop.
        """
        self.uiApp.exit()
        self._persistMRU()
        self.uiApp.finish()
        self.closeConnections()
        self._tempFileHolder.release()
        dabo_module.info(_("Application finished."))
        self._finished = True
        self.afterFinish()

    def afterFinish(self):
        """
        Stub method. When this is called, the app has already terminated, and you have
        one last chance to execute code by overriding this method.
        """
        pass

    def _destroySplash(self):
        splash = getattr(self, "_splashScreen", None)
        if splash:
            del self._splashScreen
            splash.Destroy()

    def _setProjInfo(self):
        """
        Create a 2-tuple containing the project location and project name, if any.
        The location is always the directory containing the initial startup program; the
        name is either None (default), or, if this is a Web Update-able app, the
        descriptive name.
        """
        relpth = inspect.stack()[-1][1]
        op = os.path
        pth, fnm = op.split(op.normpath(op.join(os.getcwd(), relpth)))
        projnames = {
            "ClassDesigner.py": "Class Designer",
            "CxnEditor.py": "Cxn Editor",
            "Editor.py": "Editor",
            "MenuDesigner.py": "Menu Designer",
            "PrefEditor.py": "Preference Editor",
            "ReportDesigner.py": "Report Designer",
            "DaboDemo.py": "DaboDemo",
        }
        nm = projnames.get(fnm, None)
        if nm is None:
            if "wizards" in pth:
                nm = "Wizards"
        self._projectInfo = (pth, nm)

    def getLoginInfo(self, message=None):
        """
        Return a tuple of (user, password) to dSecurityManager.login(). The default
        is to display the standard login dialog, and return the user/password as
        entered by the user, but subclasses can override to get the information from
        where ever is appropriate. You can customize the default dialog by adding
        your own code to the loginDialogHook() method, which will receive a
        reference to the login dialog.

        Return a tuple of (user, pass).
        """
        loginDialog = getattr(self, "_loginDialog", self.LoginDialogClass(self.MainForm))
        self._loginDialog = loginDialog
        loginDialog.setMessage(message)
        # Allow the developer to customize the login dialog:
        self.loginDialogHook(loginDialog)
        loginDialog.show()
        user, password = loginDialog.user, loginDialog.password
        return user, password

    def loginDialogHook(self, dlg):
        """Hook method; modify the dialog as needed."""
        pass

    def _persistMRU(self):
        """Persist any MRU lists to disk."""
        base = "MRU.%s" % self.getAppInfo("appName")
        self.deleteAllUserSettings(base)
        for cap in self._persistentMRUs:
            cleanCap = cleanMenuCaption(cap)
            mruList = self.uiApp.getMRUListForMenu(cleanCap)
            setName = ".".join((base, cleanCap))
            self.setUserSetting(setName, mruList)

    def _retrieveMRUs(self):
        """Retrieve any saved MRU lists."""
        base = "MRU.%s" % self.getAppInfo("appName")
        for cap, fcn in list(self._persistentMRUs.items()):
            cleanCap = cleanMenuCaption(cap)
            itms = self.getUserSetting(".".join((base, cleanCap)))
            if itms:
                # Should be a list of items. Add 'em in reverse order
                for itm in itms:
                    self.uiApp.addToMRU(cleanCap, itm, fcn)

    def getAppInfo(self, item, default=None):
        """Look up the item, and return the value."""
        return self._appInfo.get(item, default)

    def setAppInfo(self, item, value):
        """Set item to value in the appinfo table."""
        self._appInfo[item] = value

    def _resetWebUpdateCheck(self):
        """
        Sets the time that Web Update was last checked to the passed value. Used
        in cases where errors prevent an update from succeeding.
        """
        if self._lastCheckInfo is None:
            return
        setter, val = self._lastCheckInfo
        setter("last_check", val)

    def checkForUpdates(self, evt=None):
        """
        Public interface to the web updates mechanism. Returns a boolean
        indicating whether the update was successful.
        """
        return self.uiApp.checkForUpdates(force=True)

    def _checkForUpdates(self, force=False):
        """
        This is the actual code that checks if a) we are using Web Update; b) if we are
        due for a check; and then c) returns the status of the available updates, if any.
        """
        if not force:
            # Check for cases where we absolutely will not Web Update.
            update = settings.checkForWebUpdates
            if update:
                # Frozen App:
                if hasattr(sys, "frozen") and inspect.stack()[-1][1] != "daborun.py":
                    update = False
            if not update:
                self._setWebUpdate(False)
                return (False, {})

        # First check the framework. If it has updates available, return that info. If not,
        # see if this is an updatable project. If so, check if it has updates available, and
        # return that info.
        prf = self._frameworkPrefs
        resp = {}
        val = prf.getValue
        firstTime = not prf.hasKey("web_update")
        lastcheck = val("last_check")
        # Hold this in case the update fails.
        self._lastCheckInfo = (val, lastcheck)

        runCheck = force
        now = datetime.datetime.now()
        if not force:
            webUpdate = val("web_update")
            if webUpdate:
                checkInterval = val("update_interval")
                if checkInterval is None:
                    # Default to one day
                    checkInterval = 24 * 60
                mins = datetime.timedelta(minutes=checkInterval)
                if lastcheck is None:
                    lastcheck = datetime.datetime(1900, 1, 1)
                runCheck = now > (lastcheck + mins)

        if runCheck:
            # See if there is a later version
            url = "%s/check/%s" % (settings.webupdate_urlbase, __version__)
            try:
                resp = urllib.request.urlopen(url).read()
            except urllib.error.URLError as e:
                # Could not connect
                ### 2014-10-04, Koczian, using ustr to avoid crash
                e_uni = ustr(e)
                dabo_module.error(_("Could not connect to the Dabo servers: %s") % e_uni)
                ### 2014-10-04, Koczian, end of change
                return e
            except ValueError:
                pass
            except Exception as e:
                ### 2014-10-04, Koczian, using ustr to avoid crash
                e_uni = ustr(e)
                dabo_module.error(_("Failed to open URL '%(url)s'. Error: %(e_uni)s") % locals())
                ### 2014-10-04, Koczian, end of change
                return e
            resp = json.loads(resp)
        prf.setValue("last_check", now)
        return (firstTime, resp)

    def _updateFramework(self):
        """
        Get any changed files from the dabodev.com server, and replace
        the local copies with them.
        """
        fileurl = "%s/files/%s" % (settings.webupdate_urlbase, __version__)
        try:
            resp = urllib.request.urlopen(fileurl)
        except Exception as e:
            # No internet access, or Dabo site is down.
            dabo_module.error(_("Cannot access the Dabo site. Error: %s") % e)
            self._resetWebUpdateCheck()
            return None

        respContent = resp.read()
        if not respContent:
            # No update
            return False
        f = StringIO(respContent)
        zip = ZipFile(f)
        zipfiles = zip.namelist()
        if "DELETEDFILES" in zipfiles:
            delfiles = zip.read("DELETEDFILES").splitlines()
        else:
            delfiles = []
        if not zipfiles:
            # No updates available
            dabo_module.info(_("No changed files available."))
            return
        projects = ("dabo", "demo", "ide")
        prf = self._frameworkPrefs
        loc_demo = prf.getValue("demo_directory")
        loc_ide = prf.getValue("ide_directory")
        updates = {}
        for project in projects:
            updates[project] = [f for f in zipfiles if f.startswith(project)]
        need_demoPath = (not loc_demo) and updates["demo"]
        need_idePath = (not loc_ide) and updates["ide"]
        if need_idePath or need_demoPath:
            missing = []
            if need_demoPath and not loc_demo:
                missing.append(_("Demo path is missing"))
            if need_idePath and not loc_ide:
                missing.append(_("IDE path is missing"))
            if missing:
                return "\n".join(missing)

        locations = {"dabo": settings.root_path, "demo": loc_demo, "ide": loc_ide}
        for project in projects:
            chgs = updates[project]
            if not chgs:
                continue
            os.chdir(locations[project])
            prefix = "%s/" % project
            for pth in chgs:
                target = pth.replace(prefix, "")
                dirname = os.path.split(target)[0]
                if dirname and not os.path.exists(dirname):
                    os.makedirs(dirname)
                with open(target, "wb") as ff:
                    ff.write(zip.read(pth))
            for delfile in delfiles:
                if delfile.startswith(prefix):
                    target = delfile.replace(prefix, "")
                    shutil.rmtree(target, ignore_errors=True)
        return True

    def _setWebUpdate(self, auto, interval=None):
        """
        Sets the web update settings for the entire framework. If set to True, the
        interval is expected to be in minutes between checks.
        """
        prf = self._frameworkPrefs
        prf.setValue("web_update", auto)
        if auto:
            if interval is None:
                # They want it checked every time
                interval = 0
            prf.setValue("update_interval", interval)

    def getWebUpdateInfo(self):
        """
        Returns a 2-tuple that reflects the current settings for web updates.
        The first position is a boolean that reflects whether auto-checking is turned
        on; the second is the update frequency in minutes.
        """
        return (self._frameworkPrefs.web_update, self._frameworkPrefs.update_interval)

    def urlFetch(self, pth, errorOnNotFound=False):
        """
        Fetches the specified resource from the internet using the SourceURL value
        as the base for the resource URL. If a newer version is found, the local copy
        is updated with the retrieved resource. If the resource isn't found, nothing
        happens by default. If you want the error to be raised, pass True for the
        parameter 'errorOnNotFound'.
        """
        base = self.SourceURL
        if not base:
            # Nothing to do
            return
        u2 = urllib2
        # os.path.join works great for this; just make sure that any Windows
        # paths are converted to forward slashes, and that the
        # pth value doesn't begin with a slash
        pth = pth.lstrip(os.path.sep)
        urlparts = base.split(os.path.sep) + pth.split(os.path.sep)
        url = "/".join(urlparts)
        req = u2.Request(url)
        lastmod = self._sourceLastModified.get(url)
        resp = None
        if lastmod:
            req.add_header("If-Modified-Since", lastmod)
        elif os.path.exists(pth):
            modTime = datetime.datetime.fromtimestamp(os.stat(pth)[8])
            req.add_header("If-Modified-Since", lib.dates.webHeaderFormat(modTime))
        try:
            resp = u2.urlopen(req)
            lm = resp.headers.get("Last-Modified")
            if lm:
                self._sourceLastModified[url] = lm
        except u2.HTTPError as e:
            code = e.code
            if code in (304, 404):
                # Not changed or not found; nothing to do
                if code == 404 and errorOnNotFound:
                    # Re-raise the error
                    raise
                return
        newFile = resp.read()
        if newFile:
            with open(pth, "w") as ff:
                ff.write(newFile)
            dabo_module.info(_("File %s updated") % pth)

    def updateFromSource(self, fileOrFiles):
        """
        This method takes either a single file path or a list of paths, and if there
        is a SourceURL set, checks the source to see if there are newer versions available,
        and if so, downloads them.
        """
        if not self.SourceURL:
            # Nothing to do
            return
        if isinstance(fileOrFiles, (list, tuple)):
            for f in fileOrFiles:
                self.updateFromSource(f)
            return
        srcFile = fileOrFiles
        cwd = os.getcwd()
        # The srcFile has an absolute path; the URLs work on relative.
        try:
            splt = srcFile.split(cwd)[1].lstrip("/")
        except IndexError:
            splt = srcFile
        self.urlFetch(splt)
        try:
            nm, ext = os.path.splitext(splt)
        except ValueError:
            # No extension; skip it
            nm = ext = ""
        if ext == ".cdxml":
            # There might be an associated code file. If not, the error
            # will be caught in the app method, and no harm will be done.
            codefile = "%s-code.py" % nm
            self.urlFetch(codefile)

    def getUserSettingKeys(self, spec):
        """
        Return a list of all keys underneath <spec> in the user settings table.

        For example, if spec is "appWizard.dbDefaults", and there are
        userSettings entries for:

            appWizard.dbDefaults.pkm.Host
            appWizard.dbDefaults.pkm.User
            appWizard.dbDefaults.egl.Host

        The return value would be ["pkm", "egl"]
        """
        usp = self.UserSettingProvider
        if usp:
            return usp.getUserSettingKeys(spec)
        return None

    def getUserSetting(self, item, default=None):
        """Return the value of the item in the user settings table."""
        usp = self.UserSettingProvider
        if usp:
            return usp.getUserSetting(item, default)
        return None

    def setUserSetting(self, item, value):
        """Persist a value to the user settings file."""
        usp = self.UserSettingProvider
        if usp:
            usp.setUserSetting(item, value)

    def setUserSettings(self, setDict):
        """
        Convenience method for setting several settings with one
        call. Pass a dict containing {settingName: settingValue} pairs.
        """
        usp = self.UserSettingProvider
        if usp:
            usp.setUserSettings(setDict)

    def deleteUserSetting(self, item):
        """Removes the given item from the user settings file."""
        usp = self.UserSettingProvider
        if usp:
            usp.deleteUserSetting(item)

    def deleteAllUserSettings(self, spec):
        """Deletes all settings that begin with the supplied spec."""
        usp = self.UserSettingProvider
        if usp:
            usp.deleteAllUserSettings(spec)

    def getUserCaption(self):
        """Return the full name of the currently logged-on user."""
        if self.SecurityManager:
            return self.SecurityManager.UserCaption
        else:
            return None

    # These two methods pass encryption/decryption requests
    # to the encryption object
    def encrypt(self, val):
        """
        Takes a string or bytes and returns the encrypted string value.

        The request is passed to the Encryption object for processing, and it will handle
        encoding/decoding from strings to bytes. Note that the encrypted value will always be
        returned as a decoded string.
        """
        return self._encryption.encrypt(val)

    def decrypt(self, val):
        """
        Return decrypted string value.

        The request is passed to the Encryption object for processing. Since encryption requires
        bytes, the object will handle encoding/decoding. Note that the encrypted value will always
        be returned as a decoded string.
        """
        return self._encryption.decrypt(val)

    def getCharset(self):
        """Returns one of 'unicode' or 'ascii'."""
        return self.uiApp.charset

    def _initProperties(self):
        """Initialize the public properties of the app object."""
        self.uiType = None  # ("wx", "qt", "curses", "http", etc.)
        # self.uiModule = None

        # Initialize UI collections
        self.uiForms = Collection()
        self.uiMenus = Collection()
        self.uiToolBars = Collection()
        self.uiResources = {}

        # Initialize DB collections
        self.dbConnectionDefs = {}
        self.dbConnectionNameToFiles = {}
        self.dbConnections = {}

        self._appInfo = {}
        super()._initProperties()

    def _initDB(self, pth=None):
        """
        Set the available connection definitions for use by the app. First, read in
        all .cnxml files in the specified directory, or the current directory if none is
        specified. If no such XML definition files exist, check for a python code
        definition file named 'dbConnectionDefs.py'.
        """
        hd = self.HomeDirectory
        if not self.AutoImportConnections:
            return

        connDefs = {}
        if pth is None:
            pth = os.getcwd()
        # Import any .cnxml files in the following locations:
        #        HomeDir
        #        HomeDir/db
        #        HomeDir/data
        #        pth
        #        pth/db
        #        pth/data

        dbDirs = set(
            (
                hd,
                os.path.join(hd, "db"),
                os.path.join(hd, "data"),
                pth,
                os.path.join(pth, "db"),
                os.path.join(pth, "data"),
            )
        )
        for dbDir in dbDirs:
            if os.path.exists(dbDir) and os.path.isdir(dbDir):
                files = glob.glob(os.path.join(dbDir, "*.cnxml"))
                for f in files:
                    try:
                        cn = self.getConnectionsFromFile(f)
                    except Exception as ex:
                        uex = ustr(ex)
                        dabo_module.error(
                            _("Error loading database connection info from file %(f)s:\n%(uex)s")
                            % locals()
                        )
                    else:
                        connDefs.update(cn)
                        for kk in cn:
                            self.dbConnectionNameToFiles[kk] = f
        # Import any python code connection definitions (the "old" way).
        try:
            import dbConnectionDefs

            defs = dbConnectionDefs.getDefs()
            connDefs.update(defs)
            for kk in defs:
                self.dbConnectionNameToFiles[kk] = os.path.abspath("dbConnectionDefs.py")
        except ImportError:
            pass

        # For each connection definition, add an entry to
        # self.dbConnectionDefs that contains a key on the
        # name, and a value of a dConnectInfo object.
        for k, v in list(connDefs.items()):
            self.dbConnectionDefs[k] = v

        dabo_module.info(
            _("%s database connection definition(s) loaded.") % (len(self.dbConnectionDefs))
        )

    def _initModuleNames(self):
        """
        Import the common application-level module names into attributes
        of this application object, so that the app code can easily reference them.
        Example: if there is a 'biz' directory that can be imported, other objects in
        the system can reference bizobjs using the 'self.Application.biz' syntax
        """
        currdir = self.HomeDirectory
        currsyspath = sys.path
        if not currdir in sys.path:
            sys.path.insert(0, currdir)
        for dd in settings.standardDirs:
            currmod = getattr(self, dd, None)
            if currmod:
                # Module has already been imported; reload to get current state.
                importlib.reload(currmod)
                continue
            if sys.version.split()[0].split(".") >= ["2", "5"]:
                try:
                    self.__setattr__(dd, __import__(dd, globals(), locals(), [], 0))
                except ImportError:
                    self.__setattr__(dd, currmod)
            else:
                try:
                    (f, p, d) = importlib.util.find_spec(dd)  # imp.find_module(dd)
                    setattr(self, dd, importlib.import_module(dd, f, p, d))
                except ImportError as e:
                    self.__setattr__(dd, currmod)
        sys.path = currsyspath

    def getStandardDirectories(self):
        """Return a tuple of the fullpath to each standard directory"""
        hd = self.HomeDirectory
        subdirs = [os.path.join(hd, dd) for dd in settings.standardDirs]
        subdirs.insert(0, hd)
        return tuple(subdirs)

    def getConnectionsFromFile(self, filePath):
        """Given an absolute path to a .cnxml file, return the connection defs."""
        try:
            connDefs = connParser.importConnections(filePath, useHomeDir=True)
        except SAXParseException as e:
            dabo_module.error(_("Error parsing '%(filePath)s': %(e)s") % locals())
            return {}
        # Convert the connect info dicts to dConnectInfo instances:
        for k, v in list(connDefs.items()):
            ci = db.dConnectInfo()
            ci.setConnInfo(v)
            connDefs[k] = ci
        return connDefs

    def getConnectionByName(self, connName):
        """
        Given the name of a connection, returns the actual
        connection. Stores the connection so that multiple requests
        for the same named connection will not open multiple
        connections. If the name doesn't exist in self.dbConnectionDefs,
        then an exception is raised.
        """
        if not connName in self.dbConnections:
            if connName in self.dbConnectionDefs:
                ci = self.dbConnectionDefs[connName]
                self.dbConnections[connName] = db.dConnection(ci)
        try:
            ret = self.dbConnections[connName]
        except KeyError:
            raise exceptions.ConnectionNotFoundException(
                _("No connection named '%s' is defined") % connName
            )
        return ret

    def getConnectionNames(self):
        """Returns a list of all defined connection names"""
        return list(self.dbConnectionDefs.keys())

    def closeConnections(self):
        """Cleanup as the app is exiting."""
        for key, conn in list(self.dbConnections.items()):
            conn.close()
            del self.dbConnections[key]

    def addConnectInfo(self, ci, name=None):
        if name is None:
            try:
                name = ci.Name
            except AttributeError:
                # Use a default name
                name = "%s@%s" % (ci.User, ci.Host)
        self.dbConnectionDefs[name] = ci
        self.dbConnectionNameToFiles[name] = None

    def addConnectFile(self, connFile):
        """
        Accepts a cnxml file path, and reads in the connections
        defined in it, adding them to self.dbConnectionDefs. If the
        file cannot be found, an exception is raised.
        """
        origFile = connFile
        if not os.path.exists(connFile):
            homeFile = os.path.join(self.HomeDirectory, connFile)
            if os.path.exists(homeFile):
                connFile = homeFile
        if not os.path.exists(connFile):
            # Search sys.path for the file.
            for sp in sys.path:
                sysFile = os.path.join(sp, connFile)
                if os.path.exists(sysFile):
                    connFile = sysFile
                    break
        if os.path.exists(connFile):
            connDefs = self.getConnectionsFromFile(connFile)
            # For each connection definition, add an entry to
            # self.dbConnectionDefs that contains a key on the
            # name, and a value of a dConnectInfo object.
            for k, v in list(connDefs.items()):
                self.dbConnectionDefs[k] = v
                self.dbConnectionNameToFiles[k] = connFile
        else:
            raise IOError(_("File '%s' passed to dApp.addConnectFile() does not exist.") % origFile)

    def getStandardAppDirectory(self, dirname, start=None):
        """
        Return the path to one of the standard Dabo application directories.
        If a starting file path is provided, use that first. If not, use the
        HomeDirectory as the starting point.
        """
        stdDirs = settings.standardDirs + ("main.py",)
        if dirname not in stdDirs:
            dabo_module.error(_("Non-standard directory '%s' requested") % dirname)
            return None
        osp = os.path
        if start is not None:
            if not osp.isdir(start):
                # Use the file's directory
                start = osp.split(start)[0]
        for target in (start, self.HomeDirectory):
            if target is None:
                continue
            pth = osp.join(target, dirname)
            if osp.isdir(pth):
                return pth
            else:
                # Try the parent
                pth = osp.normpath(osp.join(target, "..", dirname))
                if osp.isdir(pth):
                    return pth
        return None

    def getTransactionToken(self, biz):
        """
        Only one bizobj at a time can begin and end transactions per connection.
        This allows the bizobj to query the app for the 'token', which is simply an
        acknowledgement that there is no other transaction pending for that connection.
        If the bizobj gets the token, further requests for the token from bizobjs using the
        same transaction will receive a reply of False, meaning that they should not be
        handling the transaction.
        """
        cn = biz._connection
        if self._transactionTokens.get(cn) is None:
            self._transactionTokens[cn] = biz
            return True
        else:
            return False

    def hasTransactionToken(self, biz):
        """
        Returns True/False, depending on whether the specified
        bizobj currently "holds" the transaction token.
        """
        cn = biz._connection
        return self._transactionTokens.get(cn) is biz

    def releaseTransactionToken(self, biz):
        """
        When a process that would normally close a transaction happens, the
        bizobj that is holding the transaction token for its connection calls this
        method to return the token. A check is run to ensure that the releasing bizobj
        is the one currently holding the token for its connection; if it is, the item is
        removed from the _transactionTokens dict.
        """
        cn = biz._connection
        if biz is self._transactionTokens.get(cn):
            del self._transactionTokens[cn]

    def setLanguage(self, lang, charset=None):
        """
        Allows you to change the language used for localization. If the language
        passed is not one for which there is a translation file, an IOError exception
        will be raised. You may optionally pass a character set to use.
        """
        self._language, self._charset = lang, charset
        localization.setLanguage(lang, charset)

    def showCommandWindow(self, context=None):
        """
        Shows a command window with a full Python interpreter.

        This is great for debugging during development, but you should turn off
        app.ShowCommandWindowMenu in production, perhaps leaving backdoor
        access to this function.

        The context argument tells dShellForm what object becomes 'self'. If not
        passed, context will be app.ActiveForm.
        """
        self.uiApp.showCommandWindow(context)

    def toggleDebugWindow(self, context=None):
        """
        Shows/hodes a debug output window. It will
        display the output of the debugging commands
        from your program.
        """
        self.uiApp.toggleDebugWindow(context)

    def fontZoomIn(self, evt=None):
        """Increase the font size on the active form."""
        self.uiApp.fontZoomIn()

    def fontZoomOut(self, evt=None):
        """Decrease the font size on the active form."""
        self.uiApp.fontZoomOut()

    def fontZoomNormal(self, evt=None):
        """Reset the font size to normal on the active form."""
        self.uiApp.fontZoomNormal()

    ########################
    # This next section simply passes menu events to the UI
    # layer to be handled there.
    def onCmdWin(self, evt):
        self.uiApp.onCmdWin(evt)

    def onDebugWin(self, evt):
        self.uiApp.onDebugWin(evt)

    def onObjectInspectorWin(self, evt):
        self.uiApp.onObjectInspectorWin(evt)

    def onWinClose(self, evt):
        self.uiApp.onWinClose(evt)

    def onFileExit(self, evt):
        self.uiApp.onFileExit(evt)

    def onEditUndo(self, evt):
        self.uiApp.onEditUndo(evt)

    def onEditRedo(self, evt):
        self.uiApp.onEditRedo(evt)

    def onEditCut(self, evt):
        self.uiApp.onEditCut(evt)

    def onEditCopy(self, evt):
        self.uiApp.onEditCopy(evt)

    def onEditPaste(self, evt):
        self.uiApp.onEditPaste(evt)

    def onEditSelectAll(self, evt):
        self.uiApp.onEditSelectAll(evt)

    def onEditFind(self, evt):
        self.uiApp.onEditFind(evt)

    def onEditFindAlone(self, evt):
        self.uiApp.onEditFindAlone(evt)

    def onEditFindAgain(self, evt):
        self.uiApp.onEditFindAgain(evt)

    def onShowSizerLines(self, evt):
        self.uiApp.onShowSizerLines(evt)

    def onReloadForm(self, evt):
        self.uiApp.onReloadForm(evt)

    def onEditPreferences(self, evt):
        af = self.ActiveForm
        if self.beforeEditPreferences() is False:
            return
        self.uiApp.onEditPreferences(evt)
        self.afterEditPreferences()
        if af:
            af.update()  ## in case setting of preferences changed VirtualField calcs

    def beforeEditPreferences(self):
        pass

    def afterEditPreferences(self):
        pass

    ############################
    # These handle MRU menu requests
    def addToMRU(self, menu, prmpt, bindfunc=None, *args, **kwargs):
        self.uiApp.addToMRU(menu, prmpt, bindfunc, *args, **kwargs)

    def onMenuOpenMRU(self, menu):
        self.uiApp.onMenuOpenMRU(menu)

    ############################
    # These methods handle AppleEvents (on Mac) and possibly other
    # similar system events caught by the uiApp object
    def onUiOpenFile(self, filename, *args, **kwargs):
        pass

    def onUiPrintFile(self, filename, *args, **kwargs):
        pass

    def onUiNewFile(self, filename, *args, **kwargs):
        pass

    def onUiReopenApp(self, filename, *args, **kwargs):
        pass

    ############################

    def copyToClipboard(self, txt):
        """Place the passed text onto the clipboard."""
        self.uiApp.copyToClipboard(txt)

    def onHelpAbout(self, evt):
        from .dock_form import dDockForm

        about = self.AboutFormClass
        if about is None:
            from ui.dialogs.htmlAbout import HtmlAbout as about
        frm = self.ActiveForm
        if frm is None:
            frm = self.MainForm
        if frm.MDI or isinstance(frm, ui.dDockForm):
            # Strange big sizing of the about form happens on Windows
            # when the parent form is MDI.
            frm = None
        dlg = about(frm)
        dlg.show()

    def addToAbout(self):
        """
        Adds additional app-specific information to the About form.
        By default, add the contents of the app's docstring.
        """
        doc = self.__class__.__doc__
        if doc != dApp.__doc__:
            return doc
        return ""

    def displayInfoMessage(self, msgId, msg, defaultShowInFuture=True):
        """
        Displays a messagebox dialog along with a checkbox for the user
        to specify whether or not to show this particular message again
        in the future.

        If user unchecks "show in future", saves that to the user's
        preference file and future calls to this function with that
        msgId will result in no message being shown.
        """
        prefKey = "display_info_messages.%s" % msgId
        if not self.getUserSetting(prefKey, True):
            return
        future = self.uiApp.displayInfoMessage(msg, defaultShowInFuture=defaultShowInFuture)
        self.setUserSetting(prefKey, future)

    def clearActiveForm(self, frm):
        """Called by the form when it is deactivated."""
        if frm is self.ActiveForm:
            self.uiApp.ActiveForm = None

    @property
    def AboutFormClass(self):
        """Specifies the form class to use for the application's About screen."""
        return getattr(self, "_aboutFormClass", None)

    @AboutFormClass.setter
    def AboutFormClass(self, val):
        self._aboutFormClass = val

    @property
    def ActiveForm(self):
        """Returns the form that currently has focus, or None.  (dForm)"""
        if hasattr(self, "uiApp") and self.uiApp is not None:
            return self.uiApp.ActiveForm
        else:
            return None

    @ActiveForm.setter
    def ActiveForm(self, frm):
        try:
            self.uiApp._setActiveForm(frm)
        except AttributeError:
            # self.uiApp hasn't been created yet.
            pass

    @property
    def AutoImportConnections(self):
        """Specifies whether .cnxml connection files are automatically imported. (Default True)"""
        return getattr(self, "_autoImportConnections", True)

    @AutoImportConnections.setter
    def AutoImportConnections(self, val):
        self._autoImportConnections = bool(val)

    @dObject.BasePrefKey.getter
    def BasePrefKey(self):
        """Override the getter for this property"""
        try:
            ret = self._basePrefKey
        except AttributeError:
            ret = self._basePrefKey = ""
        if not ret:
            try:
                ret = self.ActiveForm.BasePrefKey
            except AttributeError:
                pass
        if not ret:
            try:
                ret = self.MainForm.BasePrefKey
            except AttributeError:
                pass
        if not ret:
            dabo_module.info(_("WARNING: No BasePrefKey has been set for this application."))
            try:
                f = inspect.stack()[-1][1]
                pth = os.path.abspath(f)
            except IndexError:
                # This happens in some Class Designer forms
                pth = os.path.join(os.getcwd(), sys.argv[0])
            if pth.endswith(".py"):
                pth = pth[:-3]
            pthList = pth.strip(os.sep).split(os.sep)
            ret = ".".join(pthList)
            if isinstance(ret, bytes):
                ret = ret.decode(settings.fileSystemEncoding)
        return ret

    @property
    def CryptoKey(self):
        """
        The password and optional salt value used to secure encrypted values in your application.

        If this is a single value (str or bytes), a default salt will be used. It is recommended to
        use a 2-tuple of (password, salt), or even better, a callable that will return that 2-tuple.
        You cannot read this value, for security reasons.  Write-only.  (varies)
        """
        raise ValueError("The CryptoKey property is write-only")

    @CryptoKey.setter
    def CryptoKey(self, val):
        self._encryption.set_key(val)

    @property
    def DefaultForm(self):
        """
        The form class to open by default, automatically, after app instantiation.
        (form class reference)
        """
        return getattr(self, "_defaultForm", None)

    @DefaultForm.setter
    def DefaultForm(self, val):
        self._defaultForm = val

    @property
    def DefaultMenuBarClass(self):
        """
        The class used by all forms in the application when no specific MenuBarClass
        is specified  (ui.dMenuBar)
        """
        try:
            cls = self._defaultMenuBarClass
        except AttributeError:
            cls = self._defaultMenuBarClass = ui.dBaseMenuBar
        return cls

    @DefaultMenuBarClass.setter
    def DefaultMenuBarClass(self, val):
        self._defaultMenuBarClass = val

    @property
    def DrawSizerOutlines(self):
        """Determines if sizer outlines are drawn on the ActiveForm.  (bool)"""
        try:
            return self.uiApp.DrawSizerOutlines
        except AttributeError:
            # self.uiApp hasn't been created yet.
            return False

    @DrawSizerOutlines.setter
    def DrawSizerOutlines(self, val):
        self.uiApp.DrawSizerOutlines = val

    @property
    def Encoding(self):
        """Name of encoding to use for unicode  (str)"""
        return settings.getEncoding()

    @property
    def FormsToOpen(self):
        """List of forms to open after App instantiation.  (list of form class references)"""
        return getattr(self, "_formsToOpen", [])

    @FormsToOpen.setter
    def FormsToOpen(self, val):
        self._formsToOpen = val

    @property
    def HomeDirectory(self):
        """
        Specifies the application's home directory. (string)

        The HomeDirectory is the top-level directory for your application files, the directory
        where your main script lives. You never know what the current directory will be on a
        given system, but HomeDirectory will always get you to your files.
        """
        # start with the current directory as a default
        hd = os.getcwd()
        try:
            hd = self._homeDirectory
        except AttributeError:
            # See if we're running in Runtime Engine mode.
            try:
                hd = sys._daboRunHomeDir
            except AttributeError:
                calledScript = None
                appDir = os.path.realpath(os.path.split(inspect.getabsfile(self.__class__))[0])

                def issubdir(d1, d2):
                    while True:
                        if (len(d1) < len(d2)) or (len(d1) <= 1):
                            return False
                        d1 = os.path.split(d1)[0]
                        if d1.lower() == d2.lower():
                            return True

                if self._ignoreScriptDir:
                    if issubdir(hd, appDir):
                        hd = appDir
                    else:
                        # See if it's a child directory of a standard Dabo app structure
                        dname = os.path.basename(hd)
                        if dname in settings.standardDirs:
                            hd = os.path.dirname(hd)
                else:
                    try:
                        # Get the script name that launched the app. In case it was run
                        # as an executable, strip the leading './'
                        calledScript = sys.argv[0]
                    except IndexError:
                        # Give up... just assume the current directory.
                        hd = os.getcwd()
                    if calledScript:
                        calledScript = os.path.realpath(calledScript)
                        if calledScript.startswith("./"):
                            calledScript = calledScript.lstrip("./")
                        scriptDir = os.path.realpath(
                            os.path.split(os.path.join(os.getcwd(), calledScript))[0]
                        )
                        if issubdir(scriptDir, appDir):
                            # The directory where the main script is executing is a subdirectory of
                            # the location of the application object in use. So we can safely make
                            # the app directory the HomeDirectory.
                            hd = appDir
                        else:
                            # The directory where the main script is executing is *not* a
                            # subdirectory of the location of the app object in use. The app object
                            # is likely an instance of a raw dApp. So the only thing we can really
                            # do is make the HomeDirectory the location of the main script, since we
                            # can't guess at the application's directory structure.
                            dabo_module.info(
                                "Can't deduce HomeDirectory:setting to the script directory."
                            )
                            hd = scriptDir

            if os.path.split(hd)[1][-4:].lower() in (".zip", ".exe"):
                # mangle HomeDirectory to not be the py2exe library.zip file,
                # but the containing directory (the directory where the exe lives)
                hd = os.path.split(hd)[0]
            self._homeDirectory = hd
        return hd

    @HomeDirectory.setter
    def HomeDirectory(self, val):
        if os.path.exists(val):
            self._homeDirectory = os.path.abspath(val)
        else:
            dabo_module.error(_("Setting App HomeDirectory: Path does not exist. '%s'") % val)

    @property
    def Icon(self):
        """
        Specifies the icon to use on all forms and dialogs by default.

        The value passed can be a binary icon bitmap, a filename, or a sequence of filenames.
        Providing a sequence of filenames pointing to icons at expected dimensions like 16, 22, and
        32 px means that the system will not have to scale the icon, resulting in a much better
        appearance.
        """
        return getattr(self, "_icon", "daboIcon.ico")

    @Icon.setter
    def Icon(self, val):
        self._icon = val

    @property
    def LoginDialogClass(self):
        """The class to use for logging in."""
        defaultDialogClass = ui.dialogs.login.Login
        return getattr(self, "_loginDialogClass", defaultDialogClass)

    @LoginDialogClass.setter
    def LoginDialogClass(self, val):
        self._loginDialogClass = val

    @property
    def MainForm(self):
        """The object reference to the main form of the application, or None.

        The MainForm gets instantiated automatically during application setup,
        based on the value of MainFormClass. If you want to swap in your own
        MainForm instance, do it after setup() but before start(), as in::

        >>> from application import dApp
        >>> app = dApp()
        >>> app.setup()
        >>> app.MainForm = myMainFormInstance
        >>> app.start()

        """
        try:
            frm = self._mainForm
        except AttributeError:
            frm = None
            self._mainForm = None
        return frm

    @MainForm.setter
    def MainForm(self, val):
        self.uiApp.setMainForm(val)
        self._mainForm = val

    @property
    def MainFormClass(self):
        """Specifies the class to instantiate for the main form.

        This can be a class reference, or the path to a .cdxml file. Defaults to the dFormMain base
        class. Set to None if you don't want a main form, or set to your own main form class. Do
        this before calling dApp.start(), as in::

        >>> from application import dApp
        >>> app = dApp()
        >>> app.MainFormClass = MyMainFormClass
        >>> app.start()

        """
        try:
            cls = self._mainFormClass
        except AttributeError:
            cls = ui.dFormMain
            self._mainFormClass = cls
        return cls

    @MainFormClass.setter
    def MainFormClass(self, val):
        self._mainFormClass = val

    @property
    def NoneDisplay(self):
        """Text to display for null (None) values.  (str)"""
        v = self._noneDisplay = getattr(self, "_noneDisplay", _("< None >"))
        return v

    @NoneDisplay.setter
    def NoneDisplay(self, val):
        assert isinstance(val, str)
        self._noneDisplay = val

    @property
    def Platform(self):
        """
        Returns the platform we are running on.

        This will be one of 'Mac', 'Win' or 'GTK'.  (str)
        """
        try:
            uiApp = self.uiApp
        except AttributeError:
            uiApp = None
        if uiApp is not None:
            return self.uiApp._getPlatform()
        else:
            return "?"

    @property
    def PreferenceDialogClass(self):
        try:
            return self._preferenceDialogClass
        except AttributeError:
            # Use the default if they haven't set it
            from ui.dialogs.PreferenceDialog import PreferenceDialog

            return PreferenceDialog

    @PreferenceDialogClass.setter
    def PreferenceDialogClass(self, val):
        """
        Specifies the dialog to use for the application's user preferences.

        If None, the application will try to run the active form's onEditPreferences()
        method, if any. Otherwise, the preference dialog will be instantiated and
        shown when the user chooses to see the preferences.
        """
        self._preferenceDialogClass = val

    @property
    def ReleasePreferenceDialog(self):
        """
        Do we automatically destroy a preference dialog when closed?

        If False, the preference dialog will remain hidden in memory after closed, resulting in
        better performance when bringing up the dialog more than once.

        Note that you'll still have to handle intercepting your dialog's Close event and
        hiding it instead of releasing, or you'll be battling dead object errors.
        """
        ret = self._releasePreferenceDialog = getattr(self, "_releasePreferenceDialog", True)
        return ret

    @ReleasePreferenceDialog.setter
    def ReleasePreferenceDialog(self, val):
        self._releasePreferenceDialog = bool(val)

    @property
    def _RemoteProxy(self):
        """
        RemoteConnector when running the app remotely.

        If this bizobj is being run remotely, returns a reference to the RemoteConnector
        object that will handle communication with the server. Read-only  (RemoteConnector)
        """
        if self.SourceURL:
            try:
                return self._remoteProxy
            except AttributeError:
                self._remoteProxy = lib.RemoteConnector.RemoteConnector(self)
                return self._remoteProxy
        else:
            return None

    @property
    def SearchDelay(self):
        """
        Specifies the delay before incrementeal searching begins.  (int)

        As the user types, the search string is modified. If the time between keystrokes exceeds
        SearchDelay (milliseconds), the search will run and the search string will be cleared.

        The value set here in the Application object will become the default for all objects that
        provide incremental searching application-wide.
        """
        try:
            return self._searchDelay
        except AttributeError:
            ## I've found that a value of 300 isn't too fast nor too slow:
            # egl: 2006-11-16 - based on feedback from others, I'm
            #     lengthening this to 500 ms.
            return 500

    @SearchDelay.setter
    def SearchDelay(self, value):
        self._searchDelay = int(value)

    @property
    def SecurityManager(self):
        """
        Specifies the Security Manager, if any.

        You must subclass dSecurityManager, overriding the appropriate hooks and properties, and
        then set dApp.SecurityManager to an instance of your subclass. There is no security manager
        by default - you explicitly set this to use Dabo security.
        """
        try:
            return self._securityManager
        except AttributeError:
            return None

    @SecurityManager.setter
    def SecurityManager(self, value):
        if self.SecurityManager:
            warnings.warn(_("SecurityManager previously set"), Warning)
        self._securityManager = value

    @property
    def ShowCommandWindowMenu(self):
        """
        Specifies whether the command window option is shown in the menu.

        If True (the default), there will be a File|Command Window option available in the base
        menu. If False, your code can still start the command window by calling
        app.showCommandWindow() directly.
        """
        try:
            v = self._showCommandWindowMenu
        except AttributeError:
            v = self._showCommandWindowMenu = True
        return v

    @ShowCommandWindowMenu.setter
    def ShowCommandWindowMenu(self, val):
        self._showCommandWindowMenu = bool(val)

    @property
    def ShowSizerLinesMenu(self):
        """
        Specifies whether the "Show Sizer Lines" option is shown in the menu.

        If True (the default), there will be a View|Show Sizer Lines option available in the base
        menu.
        """
        try:
            v = self._showSizerLinesMenu
        except AttributeError:
            v = self._showSizerLinesMenu = True
        return v

    @ShowSizerLinesMenu.setter
    def ShowSizerLinesMenu(self, val):
        self._showSizerLinesMenu = bool(val)

    @property
    def SourceURL(self):
        """
        If this app's source files are updated dynamically via the web, this is the base URL to
        which the source file's name will be appended.  Default="" (i.e., no source on the
        internet).  (str)
        """
        try:
            return self._sourceURL
        except AttributeError:
            self._sourceURL = ""
            return self._sourceURL

    @SourceURL.setter
    def SourceURL(self, val):
        self._sourceURL = val

    @property
    def UserSettingProvider(self):
        """
        Specifies the reference to the object providing user preference persistence.

        The default UserSettingProvider will save user preferences inside the .dabo
        directory inside the user's home directory.
        """
        try:
            ret = self._userSettingProvider
        except AttributeError:
            if self.UserSettingProviderClass is not None:
                ret = self._userSettingProvider = self.UserSettingProviderClass()
            else:
                ret = self._userSettingProvider = None
        return ret

    @UserSettingProvider.setter
    def UserSettingProvider(self, val):
        self._userSettingProvider = val

    @property
    def UserSettingProviderClass(self):
        """
        Specifies the class to use for user preference persistence.

        The default UserSettingProviderClass will save user preferences inside the .dabo directory
        inside the user's home directory, and will be instantiated by Dabo automatically.
        """
        try:
            ret = self._userSettingProviderClass
        except AttributeError:
            ret = self._userSettingProviderClass = user_setting_provider.dUserSettingProvider
        return ret

    @UserSettingProviderClass.setter
    def UserSettingProviderClass(self, val):
        self._userSettingProviderClass = val
