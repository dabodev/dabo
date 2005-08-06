import warnings
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dButton import dButton


class dCommandButton(dButton):
	def __init__(self, *args, **kwargs):
		warnings.warn("dCommandButton is deprecated. Use dButton instead.")
		super(dCommandButton, self).__init__(*args, **kwargs)



if __name__ == "__main__":
	import test
	test.Test().runTest(dCommandButton)
