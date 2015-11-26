#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 LCI Technology Group, LLC
# All rights reserved

# This script should be run by cron and will delete old messages until there
# are no more than MAX_KEEP messages in the database. The MAX_KEEP value can
# be set in the db.py script.
import db

try:
    zdb = db.ZKMDatabase()
    zdb.cleanup_messages()

except db.DatabaseException():
    pass
