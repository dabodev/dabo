#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
import traceback

from .. import ui
from ..application import dApp
from ..dLocalize import _
from ..lib.utils import ustr
from .. import events
from ..lib.connParser import createXML
from ..lib.untabify import process as untabify
from ..ui.dialogs import WizardPage
from ..ui.dialogs import Wizard
from ..ui import dLabel
from ..ui import dSizer


def getSafeTableName(tableName):
    """Return a table name that can safely be used in generated code."""
    return tableName.title().replace(" ", "").replace(".", "_")


class AppWizardPage(WizardPage):
    pass


class PageIntro(AppWizardPage):
    def __init__(self, parent, Caption=_("Introduction")):
        super(PageIntro, self).__init__(parent=parent, Caption=Caption)

    def createBody(self):
        txt = _(
            "Use this wizard to quickly create an application "
            "for your database. Point the wizard at a database; "
            "specify a target directory; the wizard will create "
            "a full-fledged Dabo application with forms for each "
            "table in the database that allow you to run queries "
            "and edit the results. You can then edit the resulting "
            "application to fit your exact requirements. "
            "\n\n"
            "Right now Dabo supports the MySQL, Firebird, "
            "PostgreSQL, Microsoft SQL Server and SQLite databases. "
            "In time the number of supported databases will grow."
            "\n\n"
            "Press 'Next' to enter database parameters."
        )
        lbl = dabo.ui.dEditBox(
            self, Value=txt, ReadOnly=True, BorderStyle="None", BackColor=self.BackColor
        )
        self.Sizer.append1x(lbl, border=10)


class PageDatabase(AppWizardPage):
    def __init__(self, parent, Caption=_("Database Parameters")):
        super(PageDatabase, self).__init__(parent=parent, Caption=Caption)

    def createBody(self):
        self.embeddedDbTypes = ("SQLite",)
        self.embeddedFields = ("DbType", "Database", "Name")
        self.serverFields = self.embeddedFields + ("Host", "User", "Password", "Port")

        sz = self.Sizer
        lbl = dLabel(self, Caption=_("Enter the parameters here, and then click 'Next'."))
        sz.append(lbl)
        lbl = dLabel(self, Caption=_("Profile:"))

        self.dbDefaults = {}
        self.dbDefaults["MySQL"] = {
            "DbType": "MySQL",
            "Host": "dabodev.com",
            "Database": "webtest",
            "User": "webuser",
            "Password": "foxrocks",
            "Port": "3306",
            "Name": "MySQL-default",
        }
        self.dbDefaults["Firebird"] = {
            "DbType": "Firebird",
            "Host": "dabodev.com",
            "Database": "webtest",
            "User": "webuser",
            "Password": "foxrox",
            "Port": "3050",
            "Name": "Firebird-default",
        }
        self.dbDefaults["PostgreSQL"] = {
            "DbType": "PostgreSQL",
            "Host": "dabodev.com",
            "Database": "webtest",
            "User": "webuser",
            "Password": "foxrox",
            "Port": "5432",
            "Name": "PostgreSQL-default",
        }
        self.dbDefaults["MsSQL"] = {
            "DbType": "MsSQL",
            "Host": "",
            "Database": "",
            "User": "",
            "Password": "",
            "Port": "1433",
            "Name": "MsSQL-default",
        }
        self.dbDefaults["SQLite"] = {
            "DbType": "SQLite",
            "Database": "webtest.sqlite",
            "Name": "SQLite-default",
        }

        # Save the supported dbTypes into a list
        self.supportedDbTypes = list(self.dbDefaults.keys())

        # List of all fields to create for the user to select
        self.fieldNames = (
            "DbType",
            "Name",
            "Host",
            "Database",
            "User",
            "Password",
            "Port",
        )

        # Now go through the profiles that the user may have saved in the
        # user settings file:
        app = self.Application
        userProfiles = app.getUserSettingKeys("dbDefaults")
        dbDefaultKeys = list(self.dbDefaults.keys())
        dbDefaultMap = {}
        for key in dbDefaultKeys:
            dbDefaultMap[key.lower()] = key

        ## Default to MySQL first:
        defaultProfileName = "MySQL"
        defaultUserProfileName = None

        for profile in userProfiles:
            userDict = {}
            for field in self.fieldNames:
                name = "dbDefaults.%s.%s" % (profile, field)
                val = app.getUserSetting(name)
                if val is None:
                    val = ""
                userDict[field] = val
            if profile in list(dbDefaultMap.keys()):
                profile = dbDefaultMap[profile]
            self.dbDefaults[profile] = userDict

            # Override the default with the last user profile:
            defaultUserProfileName = profile

        # Set up the dropdown list based on the keys in the dbDefaults dict.
        self.ddProfile = dabo.ui.dDropdownList(self, Name="ddProfile")
        self.ddProfile.ValueMode = "string"
        self.ddProfile.Choices = list(self.dbDefaults.keys())
        if defaultUserProfileName is not None:
            self.ddProfile.Value = defaultUserProfileName
        else:
            self.ddProfile.Value = defaultProfileName
        self.ddProfile.bindEvent(events.ValueChanged, self.onProfileChoice)

        cmd = dabo.ui.dButton(self, Caption=_("New Profile..."), Name="cmdNewProfile")
        cmd.bindEvent(events.Hit, self.onNewProfile)

        gs = dabo.ui.dGridSizer()
        gs.MaxCols = 2
        gs.append(lbl)
        hs = dabo.ui.dSizer("h")
        hs.append(self.ddProfile, 1)
        hs.appendSpacer(8)
        hs.append(cmd, 0)
        gs.append(hs, "x")
        gs.appendSpacer(20, colSpan=2)
        gs.setColExpand(True, 1)

        for field in self.fieldNames:
            lbl = dLabel(self, Name=("lbl%s" % field), Width=75, Caption=("%s:" % field))
            if field == "DbType":
                obj = dabo.ui.dDropdownList(
                    self,
                    Name=("ctl%s" % field),
                    Choices=self.supportedDbTypes,
                    ValueMode="string",
                )
            else:
                pw = field.lower() == "password"
                obj = dabo.ui.dTextBox(
                    self, PasswordEntry=pw, Name=("ctl%s" % field), SelectOnEntry=True
                )
            obj.bindEvent(events.ValueChanged, self.onParmValueChanged)

            gs.append(lbl)
            # Add a file search button. It will be hidden for all
            # non-file-based backends.
            if field == "Database":
                self.btnSrch = dabo.ui.dButton(self, Caption="...")
                self.btnSrch.Width = self.btnSrch.Height * 2
                self.btnSrch.bindEvent(events.Hit, self.onDbSearch)
                hs = self.szDB = dabo.ui.dSizer("H")
                hs.append1x(obj)
                hs.append(self.btnSrch, border=10, borderSides="left")
                gs.append(hs, "x")
            else:
                gs.append(obj, "x")
        sz.append(gs, 1, "x")
        self.onProfileChoice()

    def onDbSearch(self, evt):
        """Select a file for the database"""
        pth = dabo.ui.getFile(message=_("Select the database"))
        if pth:
            self.ctlDatabase.Value = pth
            self.refresh()

    def onParmValueChanged(self, evt):
        # write the new value back to the user settings table.
        obj = evt.EventObject
        app = obj.Application
        field = obj.Name[3:]
        name = "dbDefaults.%s.%s" % (self.ddProfile.Value, field)
        app.setUserSetting(name, obj.Value)
        self.dbDefaults[self.ddProfile.Value][field] = obj.Value
        if field == "DbType":
            # User could have changed from an embedded type to a regular type, in
            # which case more/fewer fields need to be displayed:
            self.onProfileChoice()

    def onNewProfile(self, evt):
        base = _("New Profile")
        i = 1
        while True:
            default = "%s %s" % (base, i)
            if default in self.ddProfile.Choices:
                i += 1
            else:
                break

        name = dabo.ui.getString(_("Please enter a name for the profile"), defaultValue=default)
        if name is not None:
            # Defualt to the current DbType
            currDbType = self.ctlDbType.Value
            self.dbDefaults[name] = {
                "DbType": currDbType,
                "Name": "",
                "Host": "",
                "Database": "",
                "User": "",
                "Password": "",
                "Port": "",
            }
            ddProfile = self.ddProfile
            ddProfile.Choices = list(self.dbDefaults.keys())
            ddProfile.Value = name
            self.ctlDbType.Value = "MySQL"
            self.ctlPort.Value = "3306"
            self.ctlDbType.setFocus()

    def onProfileChoice(self, evt=None):
        choice = self.ddProfile.Value
        dbdefs = self.dbDefaults[choice]
        embedded = dbdefs["DbType"] in self.embeddedDbTypes
        if embedded:
            showFields = self.embeddedFields
        else:
            showFields = self.serverFields
        for fld in self.fieldNames:
            ctl = getattr(self, "ctl%s" % fld)
            if fld in showFields:
                val = dbdefs[fld]
                try:
                    ctl.Value = val
                except ValueError as e:
                    if "string must be present in the choices" in ustr(e).lower():
                        # Not sure why the saved profile dbType is empty. No time to
                        # find out why now, but at least the AW won't crash anymore.
                        pass
                    else:
                        raise
                ctl.Visible = True
            else:
                # Not a field used for this db type
                ctl.Value = None
                ctl.Visible = False
        # Enable the file search button if this is a file-based backend
        if embedded:
            self.szDB.showItem(self.btnSrch)
        else:
            self.szDB.hideItem(self.btnSrch)

    def onLeavePage(self, direction):
        if direction == "forward":
            if len(self.Form.tableDict) > 0:
                if not dabo.ui.areYouSure(_("Overwrite the current table information?")):
                    return True

            # Set the wizard's connect info based on the user input:
            ci = self.Form.connectInfo
            dbType = self.ctlDbType.Value
            try:
                ci.DbType = dbType
            except ValueError:
                dabo.ui.stop(
                    _("The database type '%s' is invalid. " + "Please reenter and try again.")
                    % dbType
                )
                self.ctlDbType.setFocus()
                return False

            embedded = dbType in self.embeddedDbTypes
            ci.Database = self.ctlDatabase.Value
            ci.Name = self.ctlName.Value
            if not embedded:
                ci.Host = self.ctlHost.Value
                ci.User = self.ctlUser.Value
                ci.Password = ci.encrypt(self.ctlPassword.Value)
                try:
                    ci.Port = int(self.ctlPort.Value)
                except ValueError:
                    ci.Port = None
            # Try to get a connection:
            busy = dabo.ui.busyInfo(_("Connecting to database..."))
            try:
                conn = dabo.db.dConnection(ci)
                cursor = self.Form.cursor = conn.getDaboCursor(ci.getDictCursorClass())
                cursor.BackendObject = ci.getBackendObject()
                tables = cursor.getTables()
            except Exception as e:
                busy = None
                traceback.print_exc()
                dabo.ui.stop(
                    _(
                        "Could not connect to the database server. "
                        + "Please check your parameters and try again."
                    )
                )
                return False
            busy = None
            self.Form.tableDict = {}
            tableOrder = 0
            for table in tables:
                # Firebird databases have system tables with '$' in the name
                if table.find("$") > -1:
                    continue
                tableDict = {}
                tableDict["name"] = table
                tableDict["order"] = tableOrder
                self.Form.tableDict[table] = tableDict
                tableOrder += 1
        return True


class PageTableSelection(AppWizardPage):
    def __init__(self, parent, Caption=_("Table Selection")):
        super(PageTableSelection, self).__init__(parent=parent, Caption=Caption)

    def createBody(self):
        self.tableSelections = {}
        txt = _(
            """The connection to the database was successful.
The following tables were found for that database.
Please check all tables you want included in
your application."""
        )
        lbl = dLabel(self, Caption=txt)
        clb = dabo.ui.dCheckList(self, Name="clbTableSelection")
        self.Sizer.append(lbl)
        self.Sizer.append1x(clb)
        hsz = dabo.ui.dSizer("h")
        btn = dabo.ui.dButton(self, Caption=_("Select All"))
        btn.bindEvent(events.Hit, self.onSelectAll)
        hsz.append(btn, border=5)
        btn = dabo.ui.dButton(self, Caption=_("Invert Selection"))
        btn.bindEvent(events.Hit, self.onInvertSelect)
        hsz.append(btn, border=5)
        btn = dabo.ui.dButton(self, Caption=_("Select None"))
        btn.bindEvent(events.Hit, self.onSelectNone)
        hsz.append(btn, border=5)
        self.Sizer.append(hsz, halign="center")

    def onEnterPage(self, direction):
        if direction == "forward":
            tbls = [t for t in self.Form.getTables()]
            tbls.sort()
            self.tableSelections = {}
            for table in tbls:
                self.tableSelections[table] = False
            tblKeys = list(self.tableSelections.keys())
            tblKeys.sort()
            self.clbTableSelection.Choices = tblKeys
            self.clbTableSelection.setFocus()

    def onSelectAll(self, evt):
        self.clbTableSelection.selectAll()

    def onSelectNone(self, evt):
        self.clbTableSelection.clearSelections()

    def onInvertSelect(self, evt):
        self.clbTableSelection.invertSelections()

    def getSelection(self):
        for choice in self.clbTableSelection.Choices:
            self.tableSelections[choice] = choice in self.clbTableSelection.Value
        return list(self.clbTableSelection.Value)

    def onLeavePage(self, direction):
        if direction == "forward":
            self.Form.selectedTables = self.getSelection()
            if not self.Form.selectedTables:
                dabo.ui.stop(
                    _(
                        "No tables were selected. "
                        + "Please select the tables you want to include in your application"
                    ),
                    title=_("No Tables Selected"),
                )
                return False
            self.fillFieldDict()
        return True

    def fillFieldDict(self):
        """Fill in the field information in the tableDict.

        We do this after the user has selected which tables to include, for
        performance reasons.
        """
        for table in self.Form.selectedTables:
            tableDict = self.Form.tableDict[table]

            fields = self.Form.cursor.getFields(table)
            tableDict["fields"] = {}
            fieldOrder = 0
            for field in fields:
                fieldName = field[0]
                tableDict["fields"][fieldName] = {}
                tableDict["fields"][fieldName]["name"] = fieldName
                tableDict["fields"][fieldName]["type"] = field[1]
                tableDict["fields"][fieldName]["order"] = fieldOrder
                tableDict["fields"][fieldName]["pk"] = field[2]
                fieldOrder += 1


class PageOutput(AppWizardPage):
    def __init__(self, parent, Caption=_("Output Options")):
        super(PageOutput, self).__init__(parent=parent, Caption=Caption)

    def createBody(self):
        self.Form._convertTabs = False
        self.Sizer.appendSpacer(5)

        lbl = dLabel(self, Caption=_("Enter the name of your app:"))
        self.txtAppName = dabo.ui.dTextBox(self)
        hs = dabo.ui.dSizer("h")
        hs.append(lbl)
        hs.appendSpacer(5)
        hs.append1x(self.txtAppName)
        self.Sizer.append(hs, "x")
        self.Sizer.appendSpacer(10)

        txt = """Enter the directory where you wish to place your
new application. It will be placed in a folder in that
directory with the application name chosen above.
You can always move the directory later."""
        lbl = dLabel(self, Caption=txt)
        self.Sizer.append(lbl)

        hs = dabo.ui.dSizer("h")
        self.txtDir = dabo.ui.dTextBox(self)
        ##pkm: Commented this out as it looks awful on Windows.
        ##self.txtDir.FontSize=10
        self.txtDir.Value = ""
        hs.append(self.txtDir, 1)
        hs.appendSpacer(4)

        self.cmdPick = dabo.ui.dButton(self, Caption="...", Width=30, Height=self.txtDir.Height)
        self.cmdPick.bindEvent(events.Hit, self.onPick)
        hs.append(self.cmdPick, 0)
        self.Sizer.append1x(hs)

        self.chkPKUI = dabo.ui.dCheckBox(self, Caption=_("Include PK fields in the UI"))
        self.Sizer.append(self.chkPKUI)

        self.chkUnknown = dabo.ui.dCheckBox(self, Caption=_("Include Unknown datatype fields"))
        self.Sizer.append(self.chkUnknown)

        self.chkSortFieldsAlpha = dabo.ui.dCheckBox(self, Caption=_("Sort Fields Alphabetically"))
        self.Sizer.append(self.chkSortFieldsAlpha)

    def onPick(self, evt):
        pth = dabo.ui.getFolder(defaultPath=self.txtDir.Value)
        if pth:
            self.txtDir.Value = pth

    def onEnterPage(self, direction):
        app = self.Application
        if direction == "forward":
            if not self.txtDir.Value:
                val = app.getUserSetting("defaultLocation")
                if not val:
                    val = os.path.abspath(os.getcwd())
                self.txtDir.Value = val
            if not self.txtAppName.Value:
                self.txtAppName.Value = self.Form.connectInfo.Database.split(os.path.sep)[-1]
            self.chkPKUI.Value = app.getUserSetting("UsePKUI", False)
            self.chkUnknown.Value = app.getUserSetting("UseUnknown", False)
            self.chkSortFieldsAlpha.Value = app.getUserSetting("SortFieldsAlpha", False)

    def onLeavePage(self, direction):
        if direction == "forward":
            # Make sure that there are values entered
            appdir = self.txtDir.Value
            appname = self.txtAppName.Value
            if not appdir or not appname:
                dabo.ui.stop(
                    _("Please enter both a name for your app and a location."),
                    _("Missing Information"),
                )
                return False
            directory = os.path.join(appdir, appname)
            if not os.path.exists(directory):
                msg = (
                    _("The target directory %s does not exist. Do you want to create it now?")
                    % directory
                )
                if dabo.ui.areYouSure(msg, _("Create Directory?"), cancelButton=False):
                    os.makedirs(directory)
                else:
                    return False
            else:
                if not os.path.isdir(directory):
                    dabo.ui.stop(
                        _(
                            "The target of '%s' is a pre-existing file, not a directory. "
                            "Please pick a different directory name."
                        )
                        % directory
                    )
                    return False
            self.Form.outputDirectory = directory
            app.setUserSetting("defaultLocation", appdir)

            self.Form.usePKUI = self.chkPKUI.Value
            self.Form.useUnknown = self.chkUnknown.Value
            self.Form.sortFieldsAlpha = self.chkSortFieldsAlpha.Value
            app.setUserSetting("UsePKUI", self.chkPKUI.Value)
            app.setUserSetting("UseUnknown", self.chkUnknown.Value)
            app.setUserSetting("SortFieldsAlpha", self.chkSortFieldsAlpha.Value)
        return True


class PageGo(AppWizardPage):
    def __init__(self, parent, Caption=_("Create Application")):
        super(PageGo, self).__init__(parent=parent, Caption=Caption)
        txt = _(
            """Press 'Finish' to create your application, or
'Back' to edit any information."""
        )
        lbl = dLabel(self, Caption=txt)
        self.Sizer.append1x(lbl)

    def onLeavePage(self, direction):
        if direction == "forward":
            if not self.Form.createApp():
                return False
            else:
                appdir = self.Form.outputDirectory
                appname = os.path.split(appdir)[-1]
                dabo.ui.info(
                    _(
                        """
Your application has been created.

To see your app in action, navigate to:
%(appdir)s
and type 'python %(appname)s.py' at the commandline.
"""
                    )
                    % locals()
                )
        return True


class AppWizard(Wizard):
    def __init__(self, parent=None, defaultDirectory=None, *args, **kwargs):
        super(AppWizard, self).__init__(parent=parent, *args, **kwargs)

        self.Caption = _("Dabo Application Wizard")
        self.Picture = "daboIcon064"
        self.Size = (520, 560)

        if defaultDirectory is None:
            self.wizDir = self.Application.HomeDirectory
        else:
            self.wizDir = defaultDirectory

        self.tableDict = {}
        self.selectedTables = []
        self.outputDirectory = ""
        self.connectInfo = dabo.db.dConnectInfo()
        self.dbType = "MySQL"  # default to MySQL
        self._convertTabs = False
        self._spacesPerTab = 4
        self.usePKUI = True
        self.useUnknown = False
        self.sortFieldsAlpha = False

        pgs = [PageIntro, PageDatabase, PageTableSelection, PageOutput, PageGo]
        self.append(pgs)
        self.layout()
        self.Centered = True
        self.start()

    def getTables(self):
        return list(self.tableDict.keys())

    def getSortedFieldNames(self, fieldDict):
        sortedFieldNames = []
        for fld in list(fieldDict.keys()):
            # next line hard to follow....
            # if we want a UI for PK's gen code for all fields,
            # if not UI for PK's, gen code for all "not PK fields"
            if self.usePKUI or not fieldDict[fld]["pk"]:
                # slightly less confusing code:
                # if we are using all filds (including unknown)
                # or the fieldtype is known (so not ?)
                # use it.
                if self.useUnknown or not fieldDict[fld]["type"] == "?":
                    if self.sortFieldsAlpha:
                        order = fieldDict[fld]["name"]
                    else:
                        order = fieldDict[fld]["order"]
                    sortedFieldNames.append((order, fld))

        sortedFieldNames.sort()
        return sortedFieldNames

    def createApp(self):
        directory = self.outputDirectory
        if os.path.exists(directory):
            td = self.tableDict
            selTb = self.selectedTables
            ci = self.connectInfo
            os.chdir(directory)
            appName = os.path.split(self.outputDirectory)[-1]
            self.appKey = ".".join(("dabo", "app", appName))

            ## Create the directory structure:
            dabo.makeDaboDirectories()

            tableName = selTb[0].title().replace(" ", "")
            formOpenString = '"Frm%s" % form_name'

            ## Create the main script:
            fname = "./%s.py" % appName
            txt = ustr(self.getMain(ci.Name, selTb[0], appName))
            with open(fname, "w") as ff:
                ff.write(txt)
            os.chmod(fname, 0o744)

            ## Create a shell script to run the main script:
            outdir = self.outputDirectory
            filecont = (
                """
# go.sh
# launches the %(appName)s app.
cd %(outdir)s
python %(appName)s.py %(tableName)s
# python %(appName)s.py --OpenAll""".strip()
                % locals()
            )
            with open("./go.sh", "w") as ff:
                ff.write(ustr(filecont))

            import stat

            os.chmod("go.sh", stat.S_IRWXU)  ## rwx for user, nothing else.

            ## Create the manifest file (for xp theme support):
            pth = os.path.join(self.wizDir, "spec-main.exe.manifest")
            with open(pth) as ff:
                txt = ustr(ff.read() % locals())
            with open("./%s.exe.manifest" % appName, "w") as ff:
                ff.write(ustr(txt))

            ## Create App.py:
            with open("./App.py", "w") as ff:
                ff.write(ustr(self.getApp(appName)))

            ## version.py:
            with open("./version.py", "w") as ff:
                ff.write(ustr(self.getVersion()))

            ## setup.py:
            with open("./setup.py", "w") as ff:
                ff.write(ustr(self.getSetup(appName)))
            with open("./buildwin.bat", "w") as ff:
                ff.write(ustr(self.getBuildwin(appName)))
            with open("./buildmac", "w") as ff:
                ff.write(ustr(self.getBuildMac(appName)))
            with open("./buildlin", "w") as ff:
                ff.write(ustr(self.getBuildLin(appName)))
            if not sys.platform.startswith("win"):
                os.system("chmod 755 ./buildmac")
                os.system("chmod 755 ./buildlin")

            # Db module:
            os.chdir("./db")
            with open("./__init__.py", "w") as ff:
                ff.write(ustr(self.getModuleInit_db()))
            with open("./default.cnxml", "w") as ff:
                ff.write(ustr(self.getDbConnXML(ci)))

            # Write the sample getDataSet:
            with open("./getSampleDataSet.py", "w") as ff:
                ff.write(ustr(self.getSampleDataSet()))

            # Biz module:
            os.chdir("../biz")

            bizImports = []
            # Write the base bizobj:
            with open("./Base.py", "w") as ff:
                ff.write(ustr(self.getBaseBizobj()))

            # Write each bizobj:
            for table in selTb:
                tableName = getSafeTableName(table)
                bizImports.append(tableName)
                with open("./%s.py" % tableName, "w") as bizfile:
                    txt = ustr(self.getBizobj(td, table))
                    bizfile.write(txt)

            with open("./__init__.py", "w") as ff:
                ff.write(ustr(self.getModuleInit_biz(bizImports)))

            # UI module:
            os.chdir("../ui")

            # Holds a list of classes that we'll import in ui/__init__.py:
            uiImports = []

            ## File|Open menu:
            with open("./MenFileOpen.py", "w") as f:
                f.write(ustr(self.getFileOpenMenu(selTb)))

            ## Reports menu:
            with open("./MenReports.py", "w") as f:
                f.write(ustr(self.getReportsMenu()))
            f.close()

            ## FrmReportBase and FrmReportSample:
            uiImports.append("FrmReportSample")
            with open("./FrmReportBase.py", "w") as f:
                f.write(ustr(self.getFrmReportBase()))
            with open("./FrmReportSample.py", "w") as f:
                f.write(ustr(self.getFrmReportSample()))

            ## base pages:
            for page in ("PagBase", "PagSelectBase", "PagEditBase"):
                with open("./%s.py" % page, "w") as f:
                    f.write(ustr(self.getPagBase(page)))

            ## base form:
            with open("./FrmBase.py", "w") as f:
                f.write(ustr(self.getFrmBase()))

            ## base grid:
            with open("./GrdBase.py", "w") as f:
                f.write(ustr(self.getGrdBase()))

            ## FrmMain:
            uiImports.append("FrmMain")
            with open("./FrmMain.py", "w") as f:
                f.write(ustr(self.getFrmMain()))

            # Write each form/grid/pageset:
            for table in selTb:
                for classType in (
                    ("Frm", self.getForm),
                    ("Grd", self.getGrd),
                    ("PagEdit", self.getPagEdit),
                    ("PagSelect", self.getPagSelect),
                ):
                    className = "%s%s" % (classType[0], getSafeTableName(table))
                    if classType[0] == "Frm":
                        uiImports.append(className)
                    with open("./%s.py" % className, "w") as f:
                        f.write(ustr(classType[1](table)))

            uiImports.sort()
            with open("./__init__.py", "w") as f:
                f.write(ustr(self.getModuleInit_ui(uiImports)))

            # reports dir:
            os.chdir("../reports")
            with open("./sampleReport.rfxml", "w") as f:
                f.write(ustr(self.getSampleReport()))

            # back to top directory:
            os.chdir("..")

            # convert to spaces if user requested it:
            if self.ConvertTabs:
                numSpaces = dabo.ui.getInt(
                    _("Enter the number of spaces for each tab:"),
                    _("Convert tabs to spaces"),
                    self.SpacesPerTab,
                )
                if numSpaces:
                    self.SpacesPerTab = numSpaces
                self._convertTabsToSpaces()
            return True

        else:
            dabo.ui.stop(_("The target directory does not exist. Cannot continue."))
            return False

    def _convertTabsToSpaces(self):
        def func(arg, dirname, fnames):
            for fname in fnames:
                if fname[-3:] == ".py":
                    untabify(
                        os.path.join(dirname, fname),
                        self.SpacesPerTab,
                        saveBackup=False,
                    )

        os.walk(".", func, None)

    def getFileOpenMenu(self, tables):
        tables.sort()
        forms = ""
        for table in tables:
            forms = "".join(
                (
                    forms,
                    """("%s", app.ui.Frm%s),\n                """
                    % (table.title(), getSafeTableName(table)),
                )
            )
        forms = "".join((forms, """("-", None),\n                """))
        with open(os.path.join(self.wizDir, "spec-MenFileOpen.py.txt")) as ff:
            return ff.read() % locals()

    def getReportsMenu(self):
        with open(os.path.join(self.wizDir, "spec-MenReports.py.txt")) as ff:
            return ff.read() % locals()

    def getForm(self, table):
        tableName = getSafeTableName(table)
        with open(os.path.join(self.wizDir, "spec-Frm.py.txt")) as ff:
            return ff.read() % locals()

    def getGrd(self, table):
        tableName = getSafeTableName(table)
        datasource = table
        colDefs = ""
        fieldDict = self.tableDict[table]["fields"]

        colDefs += """
        # Delete or comment out any columns you don't want..."""
        colSpec = """
        self.addColumn(dabo.ui.dColumn(self, DataField="%s", 
                Caption=biz.getColCaption("%s"),
                Sortable=True, Searchable=True, Editable=False))
"""
        sortedFieldNames = self.getSortedFieldNames(fieldDict)

        for tup in sortedFieldNames:
            field = tup[1]
            colDefs += colSpec % (field, field)

        with open(os.path.join(self.wizDir, "spec-Grd.py.txt")) as ff:
            return ff.read() % locals()

    def getPagEdit(self, table):
        tableName = getSafeTableName(table)
        datasource = table
        createItems = ""
        fieldDict = self.tableDict[table]["fields"]

        createItems += """
        mainSizer = self.Sizer = dabo.ui.dSizer("v")
        gs = dabo.ui.dGridSizer(VGap=7, HGap=5, MaxCols=3)
"""
        sortedFieldNames = self.getSortedFieldNames(fieldDict)

        typeConversion = {
            "I": "int",
            "C": "char",
            "M": "memo",
            "D": "date",
            "N": "float",
            "F": "float",
            "?": "char",
            "L": "blob",
            "B": "bool",
            "T": "datetime",
        }

        itemSpec = """
        ## Field %(table)s.%(fieldName)s
        label = dabo.ui.dLabel(self, NameBase="lbl%(fieldName)s", 
                    Caption=biz.getColCaption("%(labelCaption)s"))
        objectRef = %(classRef)s(self, NameBase="%(fieldName)s",
                DataSource="%(table)s", DataField="%(fieldName)s"%(ctrlCap)s,
                ToolTipText=biz.getColToolTip("%(fieldName)s"),
                HelpText=biz.getColHelpText("%(fieldName)s")
)

        gs.append(label, alignment=("top", "right") )%(memo_sizer)s
        gs.append(objectRef, "expand")
        gs.append( (25, 1) )
"""

        for tup in sortedFieldNames:
            ctrlCap = ""
            fieldName = tup[1]
            fieldInfo = fieldDict[fieldName]
            fieldType = typeConversion.get(fieldInfo["type"], "char")
            labelCaption = fieldName
            if fieldType in ["memo", "blob"]:
                classRef = "dabo.ui.dEditBox"
            elif fieldType in [
                "bool",
            ]:
                classRef = "dabo.ui.dCheckBox"
                labelCaption = ""
                ctrlCap = ', Caption=biz.getColCaption("%s")' % fieldName
            elif fieldType in [
                "date",
            ]:
                # pkm: temporary: dDateTextBox is misbehaving still. So, until we get
                #     it figured out, change the type of control used for date editing
                #     to a raw dTextBox, which can handle viewing/setting dates but
                #     doesn't have all the extra features of dDateTextBox. (2005/08/28)
                # classRef = dabo.ui.dDateTextBox
                classRef = "dabo.ui.dTextBox"
            else:
                classRef = "dabo.ui.dTextBox"
            memo_sizer = ""
            if fieldType in [
                "memo",
            ]:
                memo_sizer += """
        currRow = gs.findFirstEmptyCell()[0]
        gs.setRowExpand(True, currRow)"""
            createItems += itemSpec % locals()

        createItems += """
        gs.setColExpand(True, 1)

        mainSizer.insert(0, gs, "expand", 1, border=20)

        # Add top and bottom margins
        mainSizer.insert( 0, (-1, 10), 0)
        mainSizer.append( (-1, 20), 0)

        self.Sizer.layout()
        self.itemsCreated = True
"""

        with open(os.path.join(self.wizDir, "spec-PagEdit.py.txt")) as ff:
            return ff.read() % locals()

    def getPagSelect(self, table):
        tableName = getSafeTableName(table)

        selectOptionsPanel = ""
        fieldDict = self.tableDict[table]["fields"]

        selectOptionsPanel += '''
    def getSelectOptionsPanel(self):
        """Return the panel to contain all the select options."""

        biz = self.Form.getBizobj()
        if not biz:
            # needed for tsting
            class Biz(object):
                def getColCaption(self, caption):
                    return caption
                def getColToolTip(self, tip):
                    return tip
                def getColHelpText(self, txt):
                    return txt
            biz = Biz()

        panel = dabo.ui.dPanel(self)
        gsz = dabo.ui.dGridSizer(VGap=5, HGap=10)
        gsz.MaxCols = 3
        label = dabo.ui.dLabel(panel)
        label.Caption = _("Please enter your record selection criteria:")
        label.FontSize = label.FontSize + 2
        label.FontBold = True
        gsz.append(label, colSpan=3, alignment="center")'''
        sortedFieldNames = self.getSortedFieldNames(fieldDict)

        typeConversion = {
            "I": "int",
            "C": "char",
            "M": "memo",
            "D": "date",
            "N": "float",
            "F": "float",
            "?": "char",
            "L": "blob",
            "B": "bool",
            "T": "datetime",
        }

        itemSpec = """

        ##
        ## Field %(table)s.%(fieldName)s
        ##
        lbl = SortLabel(panel)
        lbl.Caption = biz.getColCaption("%(fieldName)s")
        lbl.relatedDataField = "%(fieldName)s"

        # Automatically get the selector options based on the field type:
        opt = self.getSelectorOptions("%(fieldType)s", wordSearch=%(wordSearch)s)

        # Add the blank choice and create the dropdown:
        opt = (IGNORE_STRING,) + tuple(opt)
        opList = SelectionOpDropdown(panel, Choices=opt)

        # Automatically get the control class based on the field type:
        ctrlClass = self.getSearchCtrlClass("%(fieldType)s")

        if ctrlClass is not None:
            ctrl = ctrlClass(panel)
            if not opList.StringValue:
                opList.PositionValue = 0
            opList.Target = ctrl

            gsz.append(lbl, halign="right")
            gsz.append(opList, halign="left")
            gsz.append(ctrl, "expand")

            # Store the info for later use when constructing the query
            self.selectFields["%(fieldName)s"] = {
                    "ctrl" : ctrl,
                    "op" : opList,
                    "type": "%(fieldType)s"
                    }
        else:
            dabo.log.error("No control class found for field '%(fieldName)s'.")
            lbl.release()
            opList.release()
"""
        for tup in sortedFieldNames:
            fieldName = tup[1]
            fieldInfo = fieldDict[fieldName]
            fieldType = typeConversion.get(fieldInfo["type"], "char")
            wordSearch = False
            if fieldType in ("memo",):
                wordSearch = True
            selectOptionsPanel += itemSpec % locals()

        selectOptionsPanel += """
        # Now add the limit field
        lbl = dabo.ui.dLabel(panel)
        lbl.Caption =  _("&Limit:")
        limTxt = SelectTextBox(panel)
        if len(limTxt.Value) == 0:
            limTxt.Value = "1000"
        self.selectFields["limit"] = {"ctrl" : limTxt}
        gsz.append(lbl, alignment="right")
        gsz.append(limTxt)

        # Custom SQL checkbox:
        chkCustomSQL = dabo.ui.dCheckBox(panel, Caption=_("Use Custom SQL"))
        chkCustomSQL.bindEvent(events.Hit, self.onCustomSQL)
        gsz.append(chkCustomSQL)

        # Requery button:
        requeryButton = dabo.ui.dButton(panel)
        requeryButton.Caption =  _("&Requery")
        requeryButton.DefaultButton = True
        requeryButton.bindEvent(events.Hit, self.onRequery)
        btnRow = gsz.findFirstEmptyCell()[0] + 1
        gsz.append(requeryButton, "expand", row=btnRow, col=1,
                halign="right", border=3)

        # Make the last column growable
        gsz.setColExpand(True, 2)
        panel.Sizer = gsz

        vsz = dabo.ui.dSizer("v")
        vsz.append(gsz, 1, "expand")
        return panel


"""
        with open(os.path.join(self.wizDir, "spec-PagSelect.py.txt")) as ff:
            return ff.read() % locals()

    def getMain(self, dbConnectionDef, table, appName):
        tableName = getSafeTableName(table)
        formOpenString = '"Frm%s" % form_name'
        with open(os.path.join(self.wizDir, "spec-main.py.txt")) as ff:
            return ff.read() % locals()

    def getSetup(self, appName):
        with open(os.path.join(self.wizDir, "spec-setup.py.txt")) as ff:
            return ff.read() % locals()

    def getBuildwin(self, appName):
        with open(os.path.join(self.wizDir, "spec-buildwin.bat")) as ff:
            return ff.read() % locals()

    def getBuildMac(self, appName):
        with open(os.path.join(self.wizDir, "spec-buildmac")) as ff:
            return ff.read() % locals()

    def getBuildLin(self, appName):
        with open(os.path.join(self.wizDir, "spec-buildlin")) as ff:
            return ff.read() % locals()

    def getModuleInit_db(self):
        with open(os.path.join(self.wizDir, "spec-db__init__.py.txt")) as ff:
            return ff.read() % locals()

    def getModuleInit_biz(self, bizImports):
        lines = ["from .%s import %s" % (class_, class_) for class_ in bizImports]
        bizInit = os.linesep.join(lines)
        with open(os.path.join(self.wizDir, "spec-biz__init__.py.txt")) as ff:
            return ff.read() % locals()

    def getModuleInit_ui(self, uiImports):
        lines = ["from .%s import %s" % (class_, class_) for class_ in uiImports]
        uiInit = os.linesep.join(lines)
        with open(os.path.join(self.wizDir, "spec-ui__init__.py.txt")) as ff:
            return ff.read() % locals()

    def getApp(self, appName):
        appName = appName.title()
        appKey = self.appKey
        with open(os.path.join(self.wizDir, "spec-App.py.txt")) as ff:
            return ff.read() % locals()

    def getDbConnXML(self, ci):
        cxnDict = {
            "dbtype": ci.DbType,
            "host": ci.Host,
            "database": ci.Database,
            "user": ci.User,
            "password": ci.Password,
            "port": ci.Port,
            "name": ci.Name,
        }
        return createXML(cxnDict, encoding="utf-8")

    def getBaseBizobj(self):
        with open(os.path.join(self.wizDir, "spec-BizBase.py.txt")) as ff:
            return ff.read()

    def getBizobj(self, tableDict, table):
        tableName = getSafeTableName(table)
        tbInfo = tableDict[table]

        # find the pk field, if any:
        pkFields = []
        for field in list(tableDict[table]["fields"].keys()):
            if tableDict[table]["fields"][field]["pk"]:
                pkFields.append(field)
        dqt = '"'
        pkField = dqt + ", ".join(pkFields) + dqt

        flds = tbInfo["fields"]

        sortedFieldNames = []
        for fld in list(flds.keys()):
            order = flds[fld]["order"]
            sortedFieldNames.append((order, fld))
        sortedFieldNames.sort()

        tableNameQt = table
        dataStructure = "        self.DataStructure = ("

        for field in sortedFieldNames:
            field_name = field[1]
            field_type = flds[field_name]["type"]
            field_pk = flds[field_name]["pk"]
            dataStructure += """
                ("%s", "%s", %s, "%s", "%s"),""" % (
                field_name,
                field_type,
                field_pk,
                tableNameQt,
                field_name,
            )
        dataStructure += "\n        )"

        with open(os.path.join(self.wizDir, "spec-Biz.py.txt")) as ff:
            return ff.read() % locals()

    def getGrdBase(self):
        with open(os.path.join(self.wizDir, "spec-GrdBase.py.txt")) as ff:
            return ff.read() % locals()

    def getFrmBase(self):
        with open(os.path.join(self.wizDir, "spec-FrmBase.py.txt")) as ff:
            return ff.read() % locals()

    def getFrmMain(self):
        with open(os.path.join(self.wizDir, "spec-FrmMain.py.txt")) as ff:
            return ff.read() % locals()

    def getFrmReportBase(self):
        with open(os.path.join(self.wizDir, "spec-FrmReportBase.py.txt")) as ff:
            return ff.read() % locals()

    def getFrmReportSample(self):
        with open(os.path.join(self.wizDir, "spec-FrmReportSample.py.txt")) as ff:
            return ff.read() % locals()

    def getPagBase(self, pageName):
        with open(os.path.join(self.wizDir, "spec-%s.py.txt" % pageName)) as ff:
            return ff.read() % locals()

    def getVersion(self):
        with open(os.path.join(self.wizDir, "spec-version.py.txt")) as ff:
            return ff.read() % locals()

    def getSampleDataSet(self):
        with open(os.path.join(self.wizDir, "spec-getSampleDataSet.py.txt")) as ff:
            return ff.read() % locals()

    def getSampleReport(self):
        with open(os.path.join(self.wizDir, "spec-sampleReport.rfxml")) as ff:
            return ff.read() % locals()

    def _onConvertTabs(evt):
        if self.Form.chkConvertTabs.Value:
            numSpaces = dabo.ui.getInt(
                _("Enter the number of spaces for each tab:"),
                _("Convert tabs to spaces"),
                4,
            )
            if numSpaces:
                self.Form._convertTabs = numSpaces
            else:
                self.Form.chkConvertTabs.Value = False
                self.Form._convertTabs = False
        else:
            self.Form._convertTabs = False

    def _getConvertTabs(self):
        return self._convertTabs

    def _setConvertTabs(self, val):
        if self._constructed():
            self._convertTabs = val
        else:
            self._properties["ConvertTabs"] = val

    def _getSpacesPerTab(self):
        return self._spacesPerTab

    def _setSpacesPerTab(self, val):
        if self._constructed():
            self._spacesPerTab = val
        else:
            self._properties["SpacesPerTab"] = val

    ConvertTabs = property(
        _getConvertTabs,
        _setConvertTabs,
        None,
        _("Do we convert tabs to spaces? Default=False  (bool)"),
    )

    SpacesPerTab = property(
        _getSpacesPerTab,
        _setSpacesPerTab,
        None,
        _("When converting tabs, the number of spaces to use per tab. Default=4  (int)"),
    )


if __name__ == "__main__":
    app = dApp(BasePrefKey="dabo.ide.wizards.AppWizard")
    app.setAppInfo("appName", "Dabo Application Wizard")
    app.setAppInfo("appShortName", "AppWizard")

    app.MainFormClass = None
    app.setup()
    wiz = AppWizard(None)

    # No need to start the app; when the wizard exits, so will the app.
