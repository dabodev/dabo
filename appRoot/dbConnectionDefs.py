# You can define any number of DB Connection definitions here.
# They will all be set up in dabo's app object for global availability

# Set up an empty dictionary
dbConnectionDefs = {}

# For each Connection Definition you want, repeat the following
# block with different keys and values:
dbConnectionDefs["Sample Connection"] = {"dbType": "MySQL", 
                                         "host": "example.com", 
                                         "user": "dabo", 
                                         "password": "dabo",
                                         "db": "sample"}

