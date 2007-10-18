# -*- coding: utf-8 -*-

import dabo
from PagEditBase import PagEditBase
from GrdOrders import GrdOrders


class PagEditCustomer(PagEditBase):
	def createItems(self):
		self.super()
		
		lProps = {"Width": 150, "Alignment": "Right"}
		fProps = {"DataSource": "customer", "Width": 75}
		borderWidth = 1

		p = self.addObject(dabo.ui.dPanel, Name="panAddress", Sizer=dabo.ui.dSizer("v"))
		p.Sizer.appendSpacer(10)

		hs = dabo.ui.dSizer("h")
		hs.append(p.addObject(dabo.ui.dLabel, Caption="Company Name:",
		                      **lProps))
		hs.append(p.addObject(dabo.ui.dTextBox, DataField="company", **fProps),
		          1, border=borderWidth)
		p.Sizer.append(hs, "expand", border=borderWidth)
		
		hs = dabo.ui.dSizer("h")
		hs.append(p.addObject(dabo.ui.dLabel, Caption="Address:", **lProps))
		hs.append(p.addObject(dabo.ui.dTextBox, DataField="address", **fProps),
		          1, border=borderWidth)
		p.Sizer.append(hs, "expand", border=borderWidth)

		hs = dabo.ui.dSizer("h")
		hs.append(p.addObject(dabo.ui.dLabel, Caption="City, Country, Postal Code:", **lProps))
		hs.append(p.addObject(dabo.ui.dTextBox, DataField="city", **fProps),
		          4, border=borderWidth)
		hs.append(p.addObject(dabo.ui.dTextBox, DataField="country", **fProps),
		          border=borderWidth)
		hs.append(p.addObject(dabo.ui.dTextBox, DataField="postalcode", **fProps),
		          2, border=borderWidth)
		p.Sizer.append(hs, "expand", border=borderWidth)

		hs = dabo.ui.dSizer("h")
		hs.append(p.addObject(dabo.ui.dLabel, Caption="Phone, Fax:", **lProps))
		hs.append(p.addObject(dabo.ui.dTextBox, DataField="phone", **fProps),
		          1, border=borderWidth)
		hs.append(p.addObject(dabo.ui.dTextBox, DataField="fax", **fProps),
		          1, border=borderWidth)
		p.Sizer.append(hs, "expand", border=borderWidth)

		hs = dabo.ui.dSizer("h")
		hs.append(p.addObject(dabo.ui.dLabel, Caption="Max Order Amt:", **lProps))
		hs.append(p.addObject(dabo.ui.dTextBox, DataField="maxordamt", **fProps),
		          border=borderWidth)
		p.Sizer.append(hs, "expand", border=borderWidth)

		hs = dabo.ui.dSizer("h")
		hs.append(p.addObject(dabo.ui.dLabel, Caption="Orders:", **lProps))
		hs.append(p.addObject(GrdOrders, RegID="grdOrders", HeaderHeight=14), 1, "expand", border=borderWidth)
		p.Sizer.append1x(hs)

		self.Sizer.append1x(p)

		self.Sizer.layout()
		self.itemsCreated = True

	def onRecordChanged(self, evt):
		print "RC"
		