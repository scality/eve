# coding: utf-8

# hack to avoid http://trac.buildbot.net/ticket/3593

path = '/usr/local/lib/python2.7/dist-packages/buildbot/db/model.py'
old_string = "'urls_json', sa.Text"
new_string = "'urls_json', sa.Text(length=2**31)"

# Read in the file
filedata = None
with open(path, 'r') as file:
    filedata = file.read()

assert old_string in filedata

# Replace the target string
filedata.replace(old_string, new_string)

# Write the file out again
with open(path, 'w') as file:
    file.write(filedata)