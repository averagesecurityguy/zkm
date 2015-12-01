# -*- coding: utf-8 -*-
#
# Copyright 2015 LCI Technology Group, LLC
# All rights reserved
import sqlite3
import logging

MAX_RETURN = 200
MAX_KEEP = 2000


# Create an exception class.
class DatabaseException(Exception):
    pass


class ZKMDatabase():
    def __init__(self):
        self.conn = sqlite3.connect('zkm.sqlite')
        self.cur = self.conn.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS messages (id integer primary key autoincrement not null , channel text, message text)")
        self.log = logging.getLogger('DB')

    def _lastrowid(self):
        """
        Get the last row id from the messages table.
        """
        self.cur.execute('SELECT max(id) from messages')
        lastrowid = self.cur.fetchone()
        return lastrowid[0]

    def get_messages(self, channel, since):
        """
        Get a list of messages whose id is greater than or equal to since.

        Log an error message and re raise it if there is a failure.
        """
        # Guarantee we do not return more than MAXMSGS for performance sake.
        if int(since) < self._lastrowid() - MAX_RETURN:
            since = self._lastrowid() - MAX_RETURN

        try:
            self.log.debug('Getting messages since {0}.'.format(since))
            self.cur.execute('SELECT * FROM messages WHERE channel=? AND id>=?', (channel, since))
            return self.cur.fetchall()

        except Exception as e:
            self.log.error('{0}'.format(e))
            raise DatabaseException('Could not get messages.')

    def get_channels(self):
        """
        Get a list of all channels on the server.

        Log an error message and re raise it if there is a failure.
        """
        try:
            self.log.debug('Getting all channels.')
            self.cur.execute('SELECT DISTINCT (channel) FROM messages')
            return self.cur.fetchall()

        except Exception as e:
            self.log.error('{0}'.format(e))
            raise DatabaseException('Could not get channels.')

    def create_message(self, channel, msg):
        """
        Add message to the database.

        Add a new message to the database. Return True if successful and False if
        not.
        """
        try:
            self.log.debug('Creating new message {0} in channel {1}.'.format(msg, channel))
            self.cur.execute('INSERT INTO messages VALUES (?, ?, ?)', (None, channel, msg))
            self.conn.commit()

        except Exception as e:
            self.log.error('{0}'.format(e))
            raise DatabaseException('Could not create a new message.')

    def cleanup_messages(self, channel):
        """
        Keep no more than MAX_KEEP messages.
        """
        try:
            discard = self._lastrowid() - MAX_KEEP

            self.log.debug('Cleaning up messages in channel {0}.'.format(channel))
            self.cur.execute('DELETE FROM messages WHERE channel=? AND id<?', (channel, discard))
            self.conn.commit()

        except Exception as e:
            self.log.error('{0}'.format(e))
            raise DatabaseException('Could not clean up messages.')
