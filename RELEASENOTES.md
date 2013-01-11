Dabo Release Notes
==================

Begun with v0.9.6 just after we migrated to GitHub from self-hosted Subversion.
For prior release notes, see https://github.com/dabodev/dabo/blob/v0.9.5/ChangeLog

v0.9.6
------
 * Improved dReportWriter's ability to locate images, especially in frozen apps.

 * Fixed some edge-cases in dReportWriter with multi-columns and spanning objects.

 * Fixed a problem with activeControlValid() for controls not bound to a bizobj.

 * Fixed a problem with dMenu running on 64-bit.

 * Tested Mac with wxPython 2.9.4.0 and fixed some obvious errors.

 * Removed biz.Caption from the EditPage.Caption.
    
 * Since the the decimal precision is already known in the bizobj, use that for dColumn.Precision if the caller didn't explicitly set it, for convenience.

 * Fixed issue introduced in v0.9.5 that tried to update invisible forms and dialogs.

