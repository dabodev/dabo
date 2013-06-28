Dabo Release Notes
==================

v0.9.13 - 28 Jun 2013
---------------------

 * dCheckBox:
  * Fixed 3-state problems and added samples to the test.
 * dGrid: 
  * Fixed to not erase the multi-selection when right-clicking.
  * Fixed wrong column sized during user resize with invisible columns.
 * dMenu:
  * Made wxPython 2.9 compatibility fixes (Thanks to Werner F Bruhin)
  * Added help strings for some menu items (Thanks to Werner F Bruhin)


v0.9.12 - 12 Jun 2013
---------------------

 * Fixed dReportWriter recursion exception in cases where the long memo text doesn't have any line breaks over the span of more than a page. Thanks to Werner F Bruhin and Carl Karsten for assisting in finding this bug.
 * Fixed dSpinner to check bounds (Value must be between Max and Min) before flushing Value to the database.
 * Code cleanup, including fixing tab/space inconsistencies (thanks Werner). 
 * Dabo v0.9.10 introduced bad locale translation files. Reverted to the translations we had prior, until we can find the long-term fix.
 * Fixed dBizobj.getDataSet() to not move the RowNumber, which it was doing if VirtualFields were involved. Fixed getDataSet() for virtual fields that need to requery children.
 * Fixed invoice progressControl demo bug in cancel. (Thanks John Fabiani).


v0.9.11 - 23 May 2013
---------------------
 * Fixed getDataSet() for virtual fields that need to requery children.
 * Convenience: return the child reference in biz.addChild().
 * Fixed some problems with the invoice report demo.


v0.9.10 - 8 May 2013
--------------------
 * Bugfix: Canceling Parent bizobj wasn't necessarily removing new child records.
 * Added better unicode handling in the operations that write out files.
 * Added ability to set default value in dApp.getAppInfo().
 * Pulled the most recent translation files from Launchpad. Thanks to everyone helping out with localizing our strings!
 * Added better buffer (blob) support.
 * Added args and kwargs to VirtualFields.
 * Added dabo.settings.convertFloatToDecimal, for when you don't want this default behavior.
 * Fixed segfaults in editable grid columns.
 * Fixed dLabel to implicitly update() when the caption changes.
 * Added getContainingPage() to get a reference to the page, if any, that contains self.


v0.9.9 - 18 Feb 2013
--------------------
 * dBizobj/dCursor: You can now specify fields that don't exist in the flds argument of getDataSet(). The returned dataset will simply not contain the missing fields.
 * dForm: Status bar was showing 'Record 1/1' with no bizobj present. Fixed.
 * dForm: In some cases, sub-forms weren't saving their window geometry correctly. Fixed.
 * List-type UI controls like dListBox and dCheckList now restore their values properly even in the presence of some bad values in the preferences file.
 * dBizobj: Added clear(), which completely clears the bizobj and its children of all data, regardless of whether there are unsaved changes.
 * dBizobj: Added removeWhere(), removeChild(), which complement addWhere() and addChild().
 * dGrid: Added property SaveRestoreDataSet. Use this to save and restore the contents of an editable grid.
 * dGrid: Fixed sorting to not sort if the grid or column is set to not be Sortable.
 * Removed self.super() and self.doDefault().
 * Removed GridHeaderPaint event.
 * Removed dabo.lib.datanav2, which has been an alias of dabo.lib.datanav for years now.


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
