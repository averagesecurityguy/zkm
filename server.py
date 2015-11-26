#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2015 LCI Technology Group, LLC
# All rights reserved

import flask
import logging

import db

#-----------------------------------------------------------------------------
# WEB SERVER
#-----------------------------------------------------------------------------
# Configure logging
logging.basicConfig(filename='server.log', level=logging.DEBUG)

app = flask.Flask(__name__)


def response(error, response):
    """
    Generate a JSON response object.
    """
    return flask.jsonify({'error': error, 'response': response})


# Every user gets every message. Not all messages can be decrypted by every
# user.
@app.route('/messages/<since>')
def get_messages(since):
    """
    Get all of the message published on or after the since value.
    """
    try:
        zdb = db.ZKMDatabase()
        msgs = zdb.get_messages(since)
        return response(None, msgs)

    except db.DatabaseException() as e:
        return response(e, None)


# Anyone can create a message.
@app.route('/message', methods=['POST'])
def create_message():
    """
    Create a new message.
    """
    try:
        zdb = db.ZKMDatabase()
        msg = flask.request.form['message']
        zdb.create_message(msg)
        response(None, 'Success')

    except db.DatabaseException() as e:
        return response(e, None)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
