""" Dabo: dynamicMenus/menuFileOpen.py
 
    This is just the default. You or the DaboWiz need to copy this
    to your application's dynamicMenus directory, and keep the structure
    but edit/add new menu entries.
    
"""

fileOpenMenuDef = { 

"items": [   
            {   
                "caption":          "Example &Submenu",
                "statusBarText":    "This is a submenu",
                "items":    [   
                                {   "caption":          "Example &Item",
                                    "statusBarText":    "This is an example item",
                                    "viewDef":          "vr_test"    },
                                
                                {   "caption":  "Another Item",
                                    "statusBarText":    "This is another example item"   }   
                            ]
            },
            {
                "caption":          "Another example submenu",
                "statusBarText":    "This is another example submenu",
                "items":    [
                                {   "caption":          "Dabo!",
                                    "statusBarText":    "Dabo dabo dabO",
                                    "viewDef":          "vr_none"    },
                                    
                                {   "caption":          "Odab",
                                    "statusBarText":    "Odab... badO backwards"    }
                            ]
            }
         ]
}
                                    
                                        
