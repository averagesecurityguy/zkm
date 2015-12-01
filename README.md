ZKM
===
ZKM is a zero knowledge messaging service. It allows small groups of people to
securely communicate without leaving metadata on the server. There is no
record of which users are communicating and the server contains no record of
when messages are posted. This prevents an adversary from building social
graphs or message time lines.


How Does It Work?
-----------------
The message database contains only an id field and a message field. A user
encrypts a message with the public key of the recipient and signs it with
their private key. The encrypted message, along with the nonce, and the
senders public key are sent to the server and stored in the database.

When reading messages, a user will pull down the last 200 messages (this is
configurable) and will decrypt and print any messages intended for them and
discard the rest. The sender's public key will be displayed as well and the
sender can be added to the contacts database.

Each user must maintain their own contact database, assigning usernames to
public keys. The server cannot maintain this information.

All encryption is based on libsodium, which uses ECC-based public/private key
pairs. If you do not have a libsodium public/private key pair one will be
generated for you on first run. If you do have a key pair, allow the system to
generate a random key pair for you on first run, then update the configuration
file with your key pair.

All configuration and contact data is stored in the .zkm directory.

Releases
--------
All Releases are code named after famous cryptographers as listed on this wiki page: https://en.wikipedia.org/wiki/List_of_cryptographers

Prerequisites
-------------
ZKM requires the following:

    * Python3
    * Flask
    * libsodium
    * pysodium
    * requests

### Installing Prerequisites Debian/Kali

    apt-get install python3 python3-pip libsodium13
    pip3 install flask requests pysodium

Some versions of Ubuntu do not have the libsodium13 package. If that is the case then you can install libsodium using the directions here:

    http://doc.libsodium.org/installation/index.html


Server Usage
------------
Either use the built-in Flask web server and configure it to use a TLS
certificate:

    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('yourserver.crt', 'yourserver.key')
    app.run(ssl_context=context)

Or configure the Flask server to run behind Apache, Nginx, or Lighttpd using
one of the many deployment options listed here:

http://flask.pocoo.org/docs/0.10/deploying/

Again, make sure you use a valid TLS certificate. Once the server running,
you can use the client to create contact lists, send messages, and receive
messages.


Client Usage
------------
When you start the client script it will check to see if the ~/.zkm directory
exists. If it does exist it will assume the initial configuration has been
completed and will continue. If it does not exist, it will create the
directory, a configuration file with a new public, secret key pair and an
empty contacts file.

Once the initial configuration is complete you will be given a `zkm >` prompt.
The first thing you need to do is run the connect command and provide the full
URL for the ZKM server with which you want to communicate. The interactive ZKM
shell supports the following commands:

### Commands

    `connect server_url` - Add the ZKM server to the configuration file.
    `add_contact name base64_encoded_public_key` - Associate a public key with a username.
    `del_contact name` - Delete a contact by name.
    `show_contacts` - List all contacts.
    `show_config` - Show the current configuration.
    `create_message username message` - Create a new message for the specified username. If the username is not listed in the contacts an error will occur.
    `read_messages` - Read all messages since last read. Will read 200 messages max.
    `quit/exit/ctrl-d` - Quit the application


Can I Use This Commercially?
----------------------------
ZKM was designed to minimize the amount of metadata stored on the server,
which requires the end user to manage their own contact list and end users who
want to communicate must manually exchange public keys. There is not public
key lookup service built in. These design decisions make it suited for small
groups of peoplel who want to communicate securely and anonymously. They also
make it difficult to scale ZKM to a large audience, which would be needed to
make it commercially viable.

With all that said, yes, the license allows you to make a commercial product
using ZKM and if you are able to solve the scale problem, I would appreciate
knowing how you did it.