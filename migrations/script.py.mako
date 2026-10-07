"""${upgrades}

${imports if imports else ''}
# past the end of the imports.

# @initech_willy - ensure we have a to_alter dict
to_alter = {}

# @initech_willy - allow a name to be specified for the table
# we are altering - we use the name passed to rename_table
# to figure out what the original table was
table_to = None
if "rename_table" in ops:
    for op in ops:
        if op[0] == "rename_table":
            to_alter[op[2]] = op[1]
            table_to = op[2]

# @initech_willy - fix up any references to the old table name
for op in ops:
    if "table_name" in op and table_to and op["table_name"] == table_to:
        op["table_name"] = to_alter[table_to]

"""
${downgrades}
