''' dActionList.py

    Define an action list, which holds a list of actions,
    keyed by name, and maps those to function objects and
    optional icons. The idea is to define an actionlist and
    then share it among one or more toolbars and/or menus.
    Functionality can be shared, and the actionList actions
    can be modified independently of menu/toolbar definitions.
    
    dApp sets up an app-wide action list which the user can
    augment, or the user can set up and maintain their own
    independent action lists.
'''

class dActionList(object):

    def __init__(self):
        object.__init__(self)
        self._actions = {}

    def getAction(self, name):
        ''' dActionList.getAction(name) -> action
        
            Return the action dictionary of the action list.
        '''
        try:
            action = self._actions[name]
        except KeyError:
            action = None
        return action
             
    def setAction(self, name, func):
        ''' dActionList.setAction(name, func) -> None
        
            Set up an action dictionary mapping name to 
            function object, and place that action dict
            into the action list for later recall.
        '''
        action = {}
        action["func"] = func
        action["icon"] = None
        action["accel"] = None
        action["toolTip"] = None
        self._actions[name] = action
        
    def doAction(self, name):
        ''' dActionList.doAction(name) -> None
        
            Find the requested action in the action list,
            and run the function associated with it.
        '''
        apply(self._actions[name]["func"])

        
if __name__ == "__main__":
    # define a few test functions:
    def function1():
        print "function1 called"
    def function2(text="hello"):
        print "function2 called with '%s'" % text
        
    # define an actionlist and some actions
    actList = dActionList()
    actList.setAction("act1", function1)
    actList.setAction("act2", function2)
    
    # test our actions:
    print "testing action 1:", actList.doAction("act1")
    print "testing action 2:", actList.doAction("act2")
    
