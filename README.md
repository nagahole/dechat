# DECHAT

My code is split into many files. However, the main files to consider are

- client.py
- server.py
- channel.py
- commons.py

An honorable mention is message.py. But it won't be included in the main files as it is simply a wrapper for encoding and decoding the protocol. Instances of the Message class will be passed around a lot in the code, and message_send and message_recv both take and output Message class instances

client.py stores the client. server.py stores the server. channel.py implements channels and commons.py holds many shared information containers and wrappers that are passed around between files.

### client.py

I encapsulated my client inside a Client class. A client instance is initiated with parameters ui_enabled (for multi-con) and log (this will pretty much always be the same as print, but for my testing, this is used as a hook to redirect output to be processed by the tester)

Once initialized, a client can be started with instance.start(). This is a non-blocking function. It is then stopped with instance.stop(). However, if the client was already reading an input() when stop() is called, it will not actually stop until an input is received.

My client.py works with many threads.

- When .start() is called, a 'main' thread is started that starts an 'input_loop' thread
- In the main thread, after the input loop thread has started, it will constantly (while it is alive) look for ClientConnectionWrappers to close. The reason it does this in the 'main' thread is when closing wrappers, it .join()s the associated sender and listener threads, which has to be done in a thread that is a parent to the sender and listener or else an error will be thrown
- The input_loop, as the name suggests, will just take input()s from the user and handle them accordingly. This loop will run non-blocking code by utilizing senders in another thread for sending messages to servers. The only time blocking code is run in the input_loop is when the user connects to a new server
- Whenever the client connects to a new server, a sender and client thread is started for that server and wrapped together in a ClientConnectionWrapper. The purpose of this is to make the multi-connections module easier. This would be unnecessary if that module was not implemented
- Listeners are always running in the background, even when one is connected to a server but not displaying it (multi-con), so that on displaying the server all the messages that would have been received will all get printed out all at once
- Similarly, senders are always running too
- When a message needs to be sent from the client to the server, the input_loop thread queues that message to be sent for the sender thread. This cross-thread communication is achieved using the ClientConnectionWrapper class
- This queue system allows the client to continue taking input while it is sending messages to the server in a separate thread without the message_send blocking the input_loop

#### Command mapping

Command maps are implemented in client_commands.py. Maps are selected accordingly to the state of the client - whether they are in a server and displaying a connection, in a server but not displaying a connection, or not in a server at all. Inputs from the input_loop are then matched against command maps to see if the client has entered a valid command

### server.py

server.py does not have a class built around it. Because of this, to pass around variables to be modified between the server.py file and server_commands.py file, in commons.py there is a ServerMembers class that is essentially an information container for every variable that would otherwise be stored on server.py. This makes passing arguments very easy as just an instance of ServerMembers (s_mems) can be passed into server_commands.py functions to run them.

Once a server is run, a separate thread is created for accepting new connections, while on the main thread, it simply loops over every connection and handles their inputs (while the server is still alive)

ServerMember attributes include:
- hostname
- port
- created_timestamp
- conns
- channels
- conn_channel_map
- nick_conn_map
- conn_nick_map
- quitted (bool)

When a command is detected from a client, it first checks if the connection is in a channel, and if it is then runs the command against the channel commands. Otherwise, if the client is not in a channel, the command is matched against the server command map in server_commands.py

### channel.py

channel.py contains a Channel class with many methods to make working with channels easier. The main methods used in channel.py includes

- .broadcast
- .welcome
- .send_message_history
- .add_connection
- .remove_connection
- .announce
- .handle_command_input

A server has an AliasDictioanry of channels. An AliasDictionary is simply an extension of the default Python dictionary I have built to make values accessible by two or more keys. This is necessary since channels can be accessed by both their IDs and their names

### commons.py

commons.py contains important information containers and wrappers. These include

- ServerMembers
- ServerConnectionInfo
- ClientStates
- ClientConnectionWrapper
- ChannelLinkInfo

## Expanding on existing code

### Adding extra commands

To add extra commands, whether on the client or server side, one can simply append to server_commands.py or client_commands.py and add the commands to the corresponding command map (a unique command map exists for each unique state of the client - for the server there is only one command map)

## How to run test-cases

I have 3 suites of test cases. One for base de-chat (no additional modules or components), one for mult-icon, and one for migration

Each suite of test cases has its own makefile rule to run them

- Base de-chat: "make test_base"
- Multicon module: "make test_multicon"
- Migration module: "make test_migration"

And to run all three of them sequentially, simply type

- "make run_tests"

## Structure of test-cases

Each test case will print the executed inputs into the client as it runs them to keep track of the progress of the tests.

I have added assertions for the most important parts of the test cases, meaning that if there are no raised exceptions at the end of each suite of test cases, then all of them have passed.

Otherwise, if there are raised exceptions when a suite has finished running, it means there are errors

I also output the client prints of each test case for each suite in log files in test/logs for more detailed debugging and testing
