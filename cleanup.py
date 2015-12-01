#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2015 LCI Technology Group, LLC
# All rights reserved

# This script should be run by cron and will delete old messages until there
# are no more than MAX_KEEP messages in the database. The MAX_KEEP value can
# be set in the db.py script.
import logging
import db

logging.basicConfig(level=logging.WARN)

try:
    zdb = db.ZKMDatabase()
    channels = zdb.get_channels()
    for channel in channels:
        zdb.cleanup_messages(channel[0])

except db.DatabaseException():
    pass
