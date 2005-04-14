## Note: as of today (1/22/2005), the dDataNav subframework is only
## compatible with wxPython, and still calls some wx functions directly,
## mostly DC related.

from Form import Form
from Grid import Grid
from Page import Page, SelectPage, EditPage, BrowsePage
from PageFrame import PageFrameMixin, PageFrame

Form = Form
Grid = Grid
Page, SelectPage, EditPage, BrowsePage = Page, SelectPage, EditPage, BrowsePage
