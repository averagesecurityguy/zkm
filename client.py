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


def load_data(filename):
    """
    Load a key:value file into a dictionary and return it.
    """
    data = {}
    with open(filename, 'rb') as f:
        for line in f:
            line = line.rstrip(b'\n')
            k, v = line.split(b'|')
            data[k] = v

    return data


def save_data(filename, data):
    """
    Save the given data to a file in key:value format.
    """
    with open(filename, 'wb') as f:
        for k, v in data.items():
            f.write(b'|'.join([k, v]))
            f.write(b'\n')


def encrypt(ssk, spk, rpk, msg):
    """
    Encrypt a message using the provided information.
    """
    ssk = base64.b64decode(ssk)
    rpk = base64.b64decode(rpk)
    nonce = pysodium.randombytes(pysodium.crypto_box_NONCEBYTES)

    enc = pysodium.crypto_box_easy(msg, nonce, rpk, ssk)

    nonce = base64.b64encode(nonce)
    enc = base64.b64encode(enc)

    # Return sender's public_key, nonce, and the encrypted message
    return b':'.join([spk, nonce, enc])


def decrypt(rsk, msg):
    """
    Decrypt a message using the provided information.
    """
    spk, nonce, enc_msg = msg.split(b':')

    spk = base64.b64decode(spk)
    rsk = base64.b64decode(rsk)
    nonce = base64.b64decode(nonce)
    enc_msg = base64.b64decode(enc_msg)

    # A ValueError is raised when decryption fails. Need to cactch it.
    try:
        dec_msg = pysodium.crypto_box_open_easy(enc_msg, nonce, spk, rsk)
    except ValueError:
        dec_msg = ''

    # Return the sender's public key and the decrypted message.
    return base64.b64encode(spk), dec_msg


def print_msg(contacts, their_public, msg):
    """
    Print the sender and message.

    Lookup the public key of the sender to see if they are in our
    contacts. If they are print the username, if not print the public key.
    """
    for username, contact_public in contacts.items():
        if their_public == contact_public:
            sender = username
        else:
            sender = their_public

    print('{0}'.format(sender.decode()))
    print('-' * len(sender))
    print(msg)


def send(server, method, endpoint, data=None):
    """
    Send a message to the server and process the response.
    """
    url = '{0}{1}'.format(server.decode(), endpoint)
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
        our_public, our_secret = pysodium.crypto_box_keypair()

        print('[+] Creating configuration file.')
        config = {b'public': base64.b64encode(our_public),
                  b'secret': base64.b64encode(our_secret),
                  b'since': b'1'}

        save_data(CONFIG, config)
        os.chmod(CONFIG, 0o600)

        print('[+] Creating contacts file.')
        save_data(CONTACT, {})
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
            self.config = load_data(CONFIG)
        except:
            print('[-] ZKM not initialized yet.')
            initialize()
            self.config = load_data(CONFIG)

        try:
            self.contacts = load_data(CONTACT)
        except Exception:
            print('[-] Could not load contacts file.')
            self.contacts = []

    def postloop(self):
        save_data(CONFIG, self.config)
        save_data(CONTACT, self.contacts)

    def do_add_contact(self, line):
        """
        Add a new contact to the contact list.
        """
        name, their_public = line.split(' ')
        self.contacts[bytes(name, 'utf8')] = bytes(their_public, 'utf8')
        save_data(CONTACT, self.contacts)

    def do_del_contact(self, name):
        """
        Remove a contact from the contact list.
        """
        self.contacts.pop(name, None)
        save_data(CONTACT, self.contacts)

    def do_connect(self, line):
        """
        Define the server we want to connect to for messages.
        """
        self.config[b'server'] = bytes(line, 'utf8')
        save_data(CONFIG, self.config)

    def do_show_config(self, line):
        """
        Print the current configuration information.
        """
        print('Current configuration')
        print('---------------------')
        print('  Public Key: {0}'.format(self.config.get(b'public')))
        print('  ZKM Server: {0}'.format(self.config.get(b'server')))
        print('  Last Check: {0}'.format(self.config.get(b'since')))
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
        username = line[0].encode()  # This will either be a username or a public key
        message = ' '.join(line[1:])

        # Return either the public key associated with the username or the
        # public key given in the command.
        their_public = self.contacts.get(username, None)

        if their_public is None:
            print('[-] No public key available for {0}.'.format(their_public))

        else:
            enc_msg = encrypt(self.config[b'secret'],
                              self.config[b'public'],
                              their_public,
                              'message: {0}'.format(message))

            resp = send(self.config[b'server'], 'POST', '/message', {'message': enc_msg})
            print('[+] {0}'.format(resp))

    def do_read_messages(self, line):
        """
        Get all messages and attempt to decrypt them.

        Use the since value stored in the configuration file. The server will
        return no more than the last 200 messages by default. This value is
        adjustable in the db.py script.
        """
        since = int(self.config.get(b'since', b'1'))
        resp = send(self.config[b'server'], 'GET', '/messages/{0}'.format(since))

        for enc_msg in resp:
            since = enc_msg[0]
            crypt = enc_msg[1].encode()  # Needs to be bytes not str

            their_public, dec_msg = decrypt(self.config[b'secret'], crypt)

            # Decryption was successful print the message
            if dec_msg.startswith('message: '):
                print_msg(self.contacts, their_public, dec_msg)

            # Update since value in the config with the next value. Need to
            # convert to bytes as well.
            self.config[b'since'] = str(since + 1).encode()

        save_data(CONFIG, self.config)

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
