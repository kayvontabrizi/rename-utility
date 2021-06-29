#!/usr/bin/env python3

# imports
import json, os, sys

# write rename dictionary to temporary file
with open(sys.argv[1], 'r') as file:
    rename = json.load(file)

# ensure the renaming dictionary does not have redundant output names
assert len(rename) == len(set(rename.values())), "Some files map to the same name!"

# rename each file in dictionary
[os.rename(old_path, new_path) for old_path, new_path in rename.items()]

# report success
print(f"Renamed {len(rename)} file(s).")
