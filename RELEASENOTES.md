Dabo Release Notes
==================

v0.9.8 - 9 Feb 2013
-------------------
 * Fixed dControlItemMixin.appendItem() to work with multiple-selections. Prior to this, calling appendItem() on a dCheckList for example would result in all the previously checked items being cleared.

 * Fixed dCursor from trying to save derived fields, which would fail. Now, we simply ignore the derived fields when saving.

 * Fixed dCursor to not persist implicit DataStructure, because different requeries can have different fields.

 * Fixed black cmd.exe box from flashing on and off in Windows in reportUtil.printReport().

 * Fixed datanav.Form where FormType="Edit", which was causing an IndexError when canceling.

 * Removed previously-deprecated dBizobj.SQL property; deprecated dBizobj.setValues() which has been going by setFieldValues() for years now.

 * Extended dBizobj.new() to accept fields to set, which will override any DefaultValues.

 * Made some sort-related minor enhancements in dBizobj and dGrid.

 * Fixed bug on Linux that made the calendar popup in dDateTextBox show in the wrong location. Also, fixed the popup to respond to key presses immediately, rather than requiring a mouse-click first.

 * Added removeColumn(), removeColumns() and addColumns() to dGrid.

 * Fixed dBizobj to only addField() when it doesn't already exist.

 * Added ProcessTabs property to dEditBox, allowing the user to type tabs into the edit box, at the expense of no longer being able to navigate to the next control with the tab key.

 * Fixed artifacts when moving dGrid columns with the mouse.

 * Fixed dApp/dSecurityManager to only instantiate one login dialog instance, instead of releasing it and reinstantiating after every failed login attempt.

 * Fixed autoBindEvents to work with Name as well as with RegID, so event handlers can be placed in the parent panel and work as expected.


v0.9.7 - 27 Jan 2013
--------------------
 * Fixed conflict between splash and login dialog.
 * Remove uuid from dabo (in stdlib now).
 * Display the appName and appVersion in About.
 * Don't cause keyboard errors in empty grids.
 * Fixed DynamicCell properties for dColumn.
 * Fixed getBizobj() to not implicitly set DataSource.
 * Fixed grid cell editing/writing back to biz.
 * Fixed makeGridEditor to not convert value to string.
 * Reworked AppWizard's generated version files.
 * Fixed the download_url in setup.py.


v0.9.6 - 11 Jan 2013
--------------------
 * Improved dReportWriter's ability to locate images, especially in frozen apps.
 * Fixed some edge-cases in dReportWriter with multi-columns and spanning objects.
 * Fixed a problem with activeControlValid() for controls not bound to a bizobj.
 * Fixed a problem with dMenu running on 64-bit.
 * Tested Mac with wxPython 2.9.4.0 and fixed some obvious errors.
 * Removed biz.Caption from the EditPage.Caption.
 * Since the the decimal precision is already known in the bizobj, use that for dColumn.Precision if the caller didn't explicitly set it, for convenience.
 * Fixed issue introduced in v0.9.5 that tried to update invisible forms and dialogs.


This file begun with v0.9.6 just after we migrated to GitHub from self-hosted Subversion. For prior release notes, see https://github.com/dabodev/dabo/blob/v0.9.5/ChangeLog
