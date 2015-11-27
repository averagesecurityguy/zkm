#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2015 LCI Technology Group, LLC
# All rights reserved

import requests
import pysodium
import os
import base64
import json
import cmd


# CONSTANTS
HOMEDIR = os.path.expanduser("~")
ZKMDIR = os.path.join(HOMEDIR, '.zkm')
CONFIG = os.path.join(ZKMDIR, 'config')
CONTACT = os.path.join(ZKMDIR, 'contacts')


def load_json_file(filename):
    """
    Load a json file into a dictionary and return it.
    """
    with open(filename, 'rb') as f:
        data = f.read()

    try:
        return json.loads(data.decode('utf8'))
    except:
        return {}


def save_json_data(filename, data):
    """
    Save the given data to a file in JSON format.
    """
    with open(filename, 'wb') as f:
        f.write('{0}\n'.format(json.dumps(data)).encode('utf8'))


def encrypt(our_secret, our_public, their_public, msg):
    """
    Encrypt a message using the provided information.
    """
    their_public = base64.b64decode(their_public)
    our_secret = base64.b64decode(our_secret)
    nonce = pysodium.randombytes(pysodium.crypto_box_NONCEBYTES)
    enc = pysodium.crypto_box(msg.encode('utf8'), nonce, their_public, our_secret)

    nonce = base64.b64encode(nonce).decode('utf8')
    enc = base64.b64encode(enc).decode('utf8')

    # Return our public_key, nonce, and the encrypted message
    return ':'.join([our_public, nonce, enc])


def decrypt(our_secret, msg):
    """
    Decrypt a message using the provided information.
    """
    our_secret = base64.b64decode(our_secret)
    their_public, nonce, enc_msg = msg.split(':')
    their_public = base64.b64decode(their_public)
    nonce = base64.b64decode(nonce)
    enc_msg = base64.b64decode(enc_msg)
    dec_msg = pysodium.crypto_box_open(enc_msg.encode('utf8'), nonce, their_public, our_secret)

    # Return the sender's public key and the decrypted message.
    return their_public, dec_msg


def print_msg(contacts, their_public, msg):
    """
    Print the sender and message.

    Lookup the public key of the sender to see if they are in our
    contacts. If they are print the username, if not print the public key.
    """
    for username, contact_public in contacts.iteritems():
        if their_public == contact_public:
            sender = username
        else:
            sender = their_public

    print('{0}: {1}'.format(sender, msg))


def send(server, method, endpoint, data=None):
    """
    Send a message to the server and process the response.
    """
    url = '{0}{1}'.format(server, endpoint)
    resp = None

    if method == 'POST':
        resp = requests.post(url, data=data)
    else:
        resp = requests.get(url, params=data)

    if resp.status_code == 200:
        j = resp.json()
        if j['error'] is not None:
            print('[-] {0}'.format(j['error']))
            return None
        else:
            return j['response']
    else:
        print('[-] Server error: {0}'.format(resp.status_code))


def initialize():
    """
    Create a ~/.zkm directory with a config file inside.

    The config file will hold our public key, secret key, and since value.
    """
    if os.path.exists(ZKMDIR) is False:
        print('[+] Creating ZKM configuration directory.')
        os.mkdir(ZKMDIR, 0o750)

        print('[+] Creating new keypair.')
        our_public, our_secret = pysodium.crypto_sign_keypair()

        print('[+] Creating configuration file.')
        config = {'public': base64.b64encode(our_public).decode('utf8'),
                  'secret': base64.b64encode(our_secret).decode('utf8'),
                  'since': 1}

        save_json_data(CONFIG, config)
        os.chmod(CONFIG, 0o600)

        print('[+] Creating contacts file.')
        save_json_data(CONTACT, {})
        os.chmod(CONTACT, 0o600)

    else:
        print('[-] ZKM configuration directory already exists.')


class ZKMClient(cmd.Cmd):
    """
    ZKM: A zero knowledge messaging system.
    """
    prompt = 'zkm> '

    # Functions used in the interactive command prompt.
    def preloop(self):
        """
        Initialize the ZKM client if necessary.
        """
        try:
            self.config = load_json_file(CONFIG)
        except:
            print('[-] ZKM not initialized yet.')
            initialize()
            self.config = load_json_file(CONFIG)

        try:
            self.contacts = load_json_file(CONTACT)
        except Exception:
            print('[-] Could not load contacts file.')
            self.contacts = []

    def postloop(self):
        save_json_data(CONFIG, self.config)
        save_json_data(CONTACT, self.contacts)

    def do_add_contact(self, line):
        """
        Add a new contact to the contact list.
        """
        name, their_public = line.split(' ')
        self.contacts[name] = their_public
        save_json_data(CONTACT, self.contacts)

    def do_del_contact(self, name):
        """
        Remove a contact from the contact list.
        """
        self.contacts.pop(name, None)
        save_json_data(CONTACT, self.contacts)

    def do_connect(self, line):
        """
        Define the server we want to connect to for messages.
        """
        self.config['server'] = line
        save_json_data(CONFIG, self.config)

    def do_show_config(self, line):
        """
        Print the current configuration information.
        """
        print('Current configuration')
        print('---------------------')
        print('  Public Key: {0}'.format(self.config.get('public')))
        print('  ZKM Server: {0}'.format(self.config.get('server')))
        print('  Last Check: {0}'.format(self.config.get('since')))
        print()

    def do_show_contacts(self, line):
        """
        Print the current list of contacts.
        """
        print('Contacts')
        print('--------')
        for contact in self.contacts:
            print('  {0}: {1}'.format(contact, self.contacts[contact]))

        print()

    def do_create_message(self, line):
        """
        Create a new encrypted message using the public key associated with
        name.
        """
        line = line.split(' ')
        username = line[0]
        message = ' '.join(line[1:])
        their_public = self.contacts.get(username, None)

        if their_public is None:
            print('[-] No public key available for {0}.'.format(their_public))

        else:
            enc_msg = encrypt(self.config['secret'],
                              self.config['public'],
                              their_public,
                              'message: {0}'.format(message))

            resp = send(self.config['server'], 'POST', '/message', {'message': enc_msg})
            print('[+] {0}'.format(resp))

    def do_read_messages(self, line):
        """
        Get all messages and attempt to decrypt them.

        Use the since value stored in the configuration file. The server will
        return no more than the last 200 messages by default. This value is
        adjustable in the db.py script.
        """
        since = self.config.get('since', 1)

        resp = send(self.config['server'], 'GET', '/messages/{0}'.format(since))

        for enc_msg in resp:
            since = enc_msg[0]
            their_public, dec_msg = decrypt(self.config['secret'], enc_msg[1])

            # Decryption was successful print the message
            if dec_msg.startswith('message: '):
                print_msg(their_public, dec_msg)

        # Update since value in the config
        self.config['since'] = since

    def do_EOF(self, line):
        """
        Usage quit | exit | ctrl-d

        Quit the ZKM client.
        """
        return True

    def do_quit(self, line):
        return True

    def do_exit(self, line):
        return True


#-----------------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------------
try:
    ZKMClient().cmdloop()

except Exception as e:
    print('[-] Error executing ZKM: {0}'.format(e))
