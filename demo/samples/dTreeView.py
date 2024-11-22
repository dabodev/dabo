# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dMenu
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dCheckBox
from dabo.ui import dTreeView
from dabo.ui import dButton

dTreeView = dabo.ui.dTreeView


class TreeViewSample(dTreeView):
    def onTreeItemContextMenu(self, evt):
        self.activeNode = evt.itemNode
        self.Form.logit(_("Context menu on node %s") % self.activeNode.Caption)

        pop = dMenu()
        pop.append(_("Add Child"), OnHit=self.onAddChild)
        pop.append(_("Add Sibling"), OnHit=self.onAddSibling)
        if not self.Editable:
            pop.append(_("Change Caption"), OnHit=self.onChangeCaption)
        pop.append(_("Delete this node"), OnHit=self.onDelNode)
        self.showContextMenu(pop)

    def onAddChild(self, evt):
        nd = self.activeNode
        self.activeNode = None
        txt = dabo.ui.getString(_("New Node Caption?"), _("Adding Child Node"))
        if txt is not None:
            nd.appendChild(txt)

    def onAddSibling(self, evt):
        nd = self.activeNode
        self.activeNode = None
        txt = dabo.ui.getString(_("New Node Caption?"), _("Adding Sibling Node"))
        if txt is not None:
            nd.parent.appendChild(txt)

    def onDelNode(self, evt):
        nd = self.activeNode
        self.activeNode = None
        self.removeNode(nd)

    def onChangeCaption(self, evt):
        nd = self.activeNode
        self.activeNode = None
        txt = dabo.ui.getString(_("New Caption"), _("Adding Child Node"), defaultValue=nd.Caption)
        if txt is not None:
            nd.Caption = txt

    def onMouseRightClick(self, evt):
        self.Form.logit(_("Mouse Right Click on tree"))

    def onTreeSelection(self, evt):
        self.Form.logit(_("Selected node caption: %s") % evt.EventData["selectedCaption"])

    def onTreeItemCollapse(self, evt):
        self.Form.logit(_("Collapsed node caption: %s") % evt.EventData["selectedCaption"])

    def onTreeItemExpand(self, evt):
        self.Form.logit(_("Expanded node caption: %s") % evt.EventData["selectedCaption"])

    def onTreeBeginDrag(self, evt):
        self.Form.logit(_("Beginning drag for %s") % evt.selectedCaption)

    def onTreeEndDrag(self, evt):
        self.Form.logit(_("Ending drag for %s") % evt.selectedCaption)


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("h", DefaultBorder=20, DefaultBorderLeft=True)
        sz.appendSpacer(25)

        self.tree = TreeViewSample(self)
        self.tree.addDummyData()
        self.tree.expandAll()
        sz.append1x(self.tree)

        # Create some controls to alter the tree's properties
        vsz = dSizer("v", DefaultSpacing=10)

        btn = dButton(self, Caption=_("Expand All"))
        btn.bindEvent(dEvents.Hit, self.onExpandAll)
        vsz.append(btn)

        btn = dButton(self, Caption=_("Collapse All"))
        btn.bindEvent(dEvents.Hit, self.onCollapseAll)
        vsz.append(btn)

        chk = dCheckBox(
            self,
            Caption=_("Show Lines"),
            DataSource="self.Parent.tree",
            DataField="ShowLines",
        )
        vsz.append(chk)

        chk = dCheckBox(
            self,
            Caption=_("Show Root Node"),
            DataSource="self.Parent.tree",
            DataField="ShowRootNode",
        )
        vsz.append(chk)

        chk = dCheckBox(
            self,
            Caption=_("Show Root Node Lines"),
            DataSource="self.Parent.tree",
            DataField="ShowRootNodeLines",
        )
        vsz.append(chk)

        chk = dCheckBox(
            self,
            Caption=_("Tree is Editable"),
            DataSource="self.Parent.tree",
            DataField="Editable",
        )
        vsz.append(chk)

        chk = dCheckBox(
            self,
            Caption=_("Mutliple Node Selection"),
            DataSource="self.Parent.tree",
            DataField="MultipleSelect",
        )
        vsz.append(chk)

        chk = dCheckBox(
            self,
            Caption=_("Show Buttons"),
            DataSource="self.Parent.tree",
            DataField="ShowButtons",
        )
        vsz.append(chk)

        sz.append1x(vsz)
        self.update()
        self.layout()

    def onExpandAll(self, evt):
        self.tree.expandAll()

    def onCollapseAll(self, evt):
        self.tree.collapseAll()


category = "Controls.dTreeView"

overview = """
<p>The <b>dTreeView</b> class is used to display hierarchical data using a branched
tree design. Branches can branch out an unlimited number of times, and
you can expand and collapse branches to show or hide detail as desired.</p>

<p>Each item is called a '<b>node</b>', and is represented by the dNode class. This class
has no meaning outside of dTreeView, so it is defined in the same file. You can
change the appearance of the node by using the same properties as any other
text-based control: FontBold, ForeColor, Caption, etc.</p>

<p>Nodes can also display icons that visually indicate what they represent; typical
examples would be a tree representing a file system, where folder and document
icons would visually represent the type of entity they are.</p>

<p>Nodes are related using family terminology, such as siblings, parents, children,
and descendants</p>
"""
