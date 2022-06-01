#!/usr/bin/env python
#
# This work is licensed under the GNU GPLv2 or later.
# See the COPYING file in the top-level directory.

# query.py: Perform a few varieties of queries

import time

import bugzilla

import requests

# public test instance of bugzilla.redhat.com. It's okay to make changes
URL = "bugzilla.mozilla.org/"

bzapi = bugzilla.Bugzilla(URL)


# build_query is a helper function that handles some bugzilla version
# incompatibility issues. All it does is return a properly formatted
# dict(), and provide friendly parameter names. The param names map
# to those accepted by Bugzilla Bug.search:
# https://bugzilla.readthedocs.io/en/latest/api/core/v1/bug.html#search-bugs

# Depending on the size of your query, you can massively speed things up
# by telling bugzilla to only return the fields you care about, since a
# large chunk of the return time is transmitting the extra bug data. You
# tweak this with include_fields:
# https://wiki.mozilla.org/Bugzilla:BzAPI#Field_Control
# Bugzilla will only return those fields listed in include_fields.
# List of available fields: summary, description, platform, severity, status, id, blocks, depends_on, creator, url, dupe_of, comments, creation_time, whiteboard, last_change_time
query = bzapi.build_query(
    product="Bugzilla",
    include_fields=["id", "summary", "status", "blocks", "severity", 'type', 'creation_time'])
t1 = time.time()
bugs = bzapi.query(query)
t2 = time.time()

res = []

print("Found %d bugs with our query" % len(bugs))

for bug in bugs:
    if bug.type == "defect":
        res.append(bug)
    if bug.id == 1588175:
        print("hi")
    if bug.id < 1600000:
        print(bug.id)

print(f"Number of defects: {len(res)}")
print(res[0].id)
print(res[0].creation_time)