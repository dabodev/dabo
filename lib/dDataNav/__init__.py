## Note: as of today (1/22/2005), the dDataNav subframework is only
## compatible with wxPython, and still calls some wx functions directly,
## mostly DC related.

from Form import Form
from Grid import Grid
from Page import Page, SelectPage, EditPage
from PageFrame import PageFrame

Form = Form
Grid = Grid
Page, SelectPage, EditPage = Page, SelectPage, EditPage
PageFrame = PageFrame
