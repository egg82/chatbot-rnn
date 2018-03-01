from chatbot import libchatbot
import discord
import os
import json

try: # Unicode patch for Windows
    import win_unicode_console
    win_unicode_console.enable()
except:
    if os.name == 'nt':
        import sys
        if sys.version_info < (3,6):
            print("Please install the 'win_unicode_console' module.")

do_logging = True
log_name = "Discord-Chatbot.log"

states_main = "states"
states_folder = states_main + "/" + "server_states"
states_folder_dm = states_main + "/" + "dm_states"

autosave = True
autoload = True
max_length = 500

user_settings_folder = "user_settings"
ult_operators_file = user_settings_folder + "/" + "ult_operators.cfg"
operators_file = user_settings_folder + "/" + "operators.cfg"
banned_users_file = user_settings_folder + "/" + "banned_users.cfg"

processing_users = {}

mention_in_message = True
mention_message_separator = " - "

ult_operators = []
operators = []
banned_users = []

states_queue = {}

print('Loading Chatbot-RNN...')
save, load, get, get_current, reset, consumer = libchatbot(max_length=max_length)
print('Chatbot-RNN has been loaded.')

print('Preparing Discord Bot...')
client = discord.Client()

@client.event
async def on_ready():
    print()
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print()
    print('Discord Bot ready!')

def log(message):
    if do_logging:
        with open(log_name, "a", encoding="utf-8") as log_file:
            log_file.write(message)

def load_channel_states(channel):
    global states_folder, states_folder_dm, load, reset

    make_folders()
    
    states_file = get_states_file(channel)
        
    if os.path.exists(states_file + ".pkl") and os.path.isfile(states_file + ".pkl"):
        return get(states_file)
    else:
        return reset()

def make_folders():
    if not os.path.exists(states_folder):
        os.makedirs(states_folder)

    if not os.path.exists(states_folder_dm):
        os.makedirs(states_folder_dm)

    if not os.path.exists(user_settings_folder):
        os.makedirs(user_settings_folder)

def get_states_file(channel):
    if channel.is_private:
        states_file = states_folder_dm + "/" + channel.id
    else:
        states_file = states_folder + "/" + channel.id

    return states_file

def save_channel_states(channel): # Depricated, use states queue now
    global states_folder, states_folder_dm, save

    make_folders()

    states_file = get_states_file(channel)
    
    save(states_file)

def add_states_to_queue(channel, states_diffs):
    current_states_diffs = None
    
    if channel in states_queue:
        current_states_diffs = states_queue[channel]

    for num in range(len(states_diffs)):
        if not current_states_diffs == None and not current_states_diffs[num] == None:
            states_diffs[num] += current_states_diffs[num]
    
    states_queue.update({channel:states_diffs})

def write_state_queue():
    for channel in states_queue:
        states = load_channel_states(channel)
        new_states = states
        
        states_diff = states_queue[channel]
        total_num = 0
        for num in range(len(states)):
            for num_two in range(len(states[num])):
                for num_three in range(len(states[num][num_two])):
                    for num_four in range(len(states[num][num_two][num_three])):
                        new_states[num][num_two][num_three][num_four] = states[num][num_two][num_three][num_four] - states_diff[total_num]
                        total_num += 1
            
        save(get_states_file(channel), states=new_states)
    states_queue.clear()

def is_discord_id(user_id):
    # Quick general check to see if it matches the ID formatting
    return user_id.isdigit and len(user_id) == 18

def remove_invalid_ids(id_list):
    for user in id_list:
        if not is_discord_id(user):
            id_list.remove(user)

def save_ops_bans():
    global ult_operators, operators, banned_users

    make_folders()

    # Sort and remove duplicate entries
    ult_operators = list(set(ult_operators))
    operators = list(set(operators))
    banned_users = list(set(banned_users))

    # Remove from list if ID is invalid
    remove_invalid_ids(ult_operators)

    # Remove them from the ban list if they were added
    # Op them if they were removed
    for user in ult_operators:
        operators.append(user)
        if user in banned_users:
            banned_users.remove(user)

    # Remove from list if ID is invalid
    remove_invalid_ids(operators)

    # Remove from list if ID is invalid
    remove_invalid_ids(banned_users)

    # Sort and remove duplicate entries
    ult_operators = list(set(ult_operators))
    operators = list(set(operators))
    banned_users = list(set(banned_users))

    with open(ult_operators_file, 'w') as f:
        f.write(json.dumps(ult_operators))
    with open(operators_file, 'w') as f:
        f.write(json.dumps(operators))
    with open(banned_users_file, 'w') as f:
        f.write(json.dumps(banned_users))

def load_ops_bans():
    global ult_operators, operators, banned_users

    make_folders()

    if os.path.exists(ult_operators_file) and os.path.isfile(ult_operators_file):
        with open(ult_operators_file, 'r') as f:
            try:
                ult_operators = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                ult_operators = []

    if os.path.exists(operators_file) and os.path.isfile(operators_file):
        with open(operators_file, 'r') as f:
            try:
                operators = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                operators = []

    if os.path.exists(banned_users_file) and os.path.isfile(banned_users_file):
        with open(banned_users_file, 'r') as f:
            try:
                banned_users = json.loads(f.read())
            except json.decoder.JSONDecodeError:
                banned_users = []

    save_ops_bans()

# Prepare the operators and ban lists
load_ops_bans()

async def process_command(msg_content, message):
    user_command_entered = False
    response = ""

    load_ops_bans()

    if message.author.id in banned_users and not message.channel.is_private:
        user_command_entered = True
        
        response = "Sorry, you have been banned."
    else:
        # Operators and DMs can use these commands
        if msg_content.startswith('--reset'):
            user_command_entered = True
            if message.author.id in operators or message.channel.is_private:
                reset()
                save_channel_states(message.channel)
                print()
                print("[Model state reset]")
                response = "Model state reset."
            else:
                response = "Insufficient permissions."
                
        # Operators can use these commands
        elif msg_content.startswith('--basicreset'):
            user_command_entered = True
            if message.author.id in operators:
                reset()
                print()
                print("[Model state reset (basic)]")
                response = "Model state reset (basic)."
            else:
                response = "Insufficient permissions."
        
        elif msg_content.startswith('--save '):
            user_command_entered = True
            if message.author.id in operators:
                input_text = msg_content[len('--save '):]
                save(input_text)
                print()
                print("[Saved states to \"{}.pkl\"]".format(input_text))
                response = "Saved model state to \"{}.pkl\".".format(input_text)
            else:
                response = "Insufficient permissions."
        
        elif msg_content.startswith('--load '):
            user_command_entered = True
            if message.author.id in operators:
                input_text = msg_content[len('--load '):]
                load(input_text)
                print()
                print("[Loaded saved states from \"{}.pkl\"]".format(input_text))
                response = "Loaded saved model state from \"{}.pkl\".".format(input_text)
            else:
                response = "Insufficient permissions."

        elif msg_content.startswith('--autosaveon'):
            user_command_entered = True
            if message.author.id in operators:
                if not autosave:
                    autosave = True
                    print()
                    print("[Turned on autosaving]")
                    response = "Turned on autosaving."
                else:
                    response = "Autosaving is already on."
            else:
                response = "Insufficient permissions."
        
        elif msg_content.startswith('--autosaveoff'):
            user_command_entered = True
            if message.author.id in operators:
                if autosave:
                    autosave = False
                    print()
                    print("[Turned off autosaving]")
                    response = "Turned off autosaving."
                else:
                    response = "Autosaving is already off."
            else:
                response = "Insufficient permissions."
        
        elif msg_content.startswith('--autoloadton'):
            user_command_entered = True
            if message.author.id in operators:
                if not autoload:
                    autoload = True
                    print()
                    print("[Turned on autoloading]")
                    response = "Turned on autoloading."
                else:
                    response = "Autoloading is already on."
            else:
                response = "Insufficient permissions."
        
        elif msg_content.startswith('--autoloadoff'):
            user_command_entered = True
            if message.author.id in operators:
                if autoload:
                    autoload = False
                    print()
                    print("[Turned off autoloading]")
                    response = "Turned off autoloading."
                else:
                    response = "Autoloading is already off."
            else:
                response = "Insufficient permissions."

        elif msg_content.startswith('--op '):
            user_command_entered = True
            if message.author.id in operators:
                # Replacements are to support mentioned users
                input_text = msg_content[len('--op '):].replace('<@', '').replace('!', '').replace('>', '')
                user_exists = True
                
                # Check if user actually exists
                try:
                    await client.get_user_info(input_text)
                except discord.NotFound:
                    user_exists = False
                except discord.HTTPException:
                    user_exists = False
                
                if not input_text in ult_operators and user_exists:
                    load_ops_bans()
                    operators.append(input_text)
                    save_ops_bans()
                    print()
                    print("[Opped \"{}\"]".format(input_text))
                    response = "Opped \"{}\".".format(input_text)
                else:
                    response = "Unable to op user \"{}\".".format(input_text)
            else:
                response = "Insufficient permissions."

        elif msg_content.startswith('--deop '):
            user_command_entered = True
            if message.author.id in operators:
                # Replacements are to support mentioned users
                input_text = msg_content[len('--deop '):].replace('<@', '').replace('!', '').replace('>', '')
                user_exists = True
                
                # Check if user actually exists
                try:
                    await client.get_user_info(input_text)
                except discord.NotFound:
                    user_exists = False
                except discord.HTTPException:
                    user_exists = False
                
                if not input_text in ult_operators and user_exists:
                    load_ops_bans()
                    if input_text in operators:
                        operators.remove(input_text)
                    save_ops_bans()
                    print()
                    print("[De-opped \"{}\"]".format(input_text))
                    response = "De-opped \"{}\".".format(input_text)
                else:
                    response = "Unable to de-op user \"{}\".".format(input_text)
            else:
                response = "Insufficient permissions."

        elif msg_content.startswith('--ban '):
            user_command_entered = True
            if message.author.id in operators:
                # Replacements are to support mentioned users
                input_text = msg_content[len('--ban '):].replace('<@', '').replace('!', '').replace('>', '')
                user_exists = True
                
                # Check if user actually exists
                try:
                    await client.get_user_info(input_text)
                except discord.NotFound:
                    user_exists = False
                except discord.HTTPException:
                    user_exists = False
                
                if not input_text in ult_operators and user_exists:
                    load_ops_bans()
                    banned_users.append(input_text)
                    save_ops_bans()
                    print()
                    print("[Banned \"{}\"]".format(input_text))
                    response = "Banned \"{}\".".format(input_text)
                else:
                    response = "Unable to ban user \"{}\".".format(input_text)
            else:
                response = "Insufficient permissions."

        elif msg_content.startswith('--unban '):
            user_command_entered = True
            if message.author.id in operators:
                # Replacements are to support mentioned users
                input_text = msg_content[len('--unban '):].replace('<@', '').replace('!', '').replace('>', '')
                user_exists = True
                
                # Check if user actually exists
                try:
                    await client.get_user_info(input_text)
                except discord.NotFound:
                    user_exists = False
                except discord.HTTPException:
                    user_exists = False
                
                if not input_text in ult_operators and user_exists:
                    load_ops_bans()
                    if input_text in banned_users:
                        banned_users.remove(input_text)
                    save_ops_bans()
                    print()
                    print("[Un-banned \"{}\"]".format(input_text))
                    response = "Un-banned \"{}\".".format(input_text)
                else:
                    response = "Unable to un-ban user \"{}\".".format(input_text)
            else:
                response = "Insufficient permissions."
    
    return user_command_entered, response

async def set_typing(message):
    await client.send_typing(message.channel)

async def send_message(message, text):
    if not text == '':
        if mention_in_message:
            user_mention = "<@" + message.author.id + ">" + mention_message_separator
        else:
            user_mention = ""
        await client.send_message(message.channel, user_mention + text)

@client.event
async def on_message(message):
    global save, load, get, get_current, reset, consumer, states_file, autosave
    
    if (message.content.startswith('>') or message.channel.is_private) and not message.author.bot:
        msg_content = message.content
        if message.content.startswith('> '):
            msg_content = message.content[len('> '):]
        elif message.content.startswith('>'):
            msg_content = message.content[len('>'):]

        await set_typing(message)

        # Run this out of empty checks to see if the user is banned, first
        user_command_entered, response = await process_command(msg_content, message)

        if user_command_entered:
            await send_message(message, response)
        else:
            if not (message.author.id in processing_users and message.channel.id in processing_users[message.author.id]):
                if not msg_content == '':
                    if not len(msg_content) > max_length:
                        # Possibly problematic: if something goes wrong,
                        # then the user couldn't send messages anymore
                        if message.author.id in processing_users:
                            user_channels = processing_users[message.author.id]
                            user_channels.append(message.channel.id)
                        else:
                            processing_users.update({message.author.id:[message.channel.id]})
                        
                        if autoload:
                            states = load_channel_states(message.channel)
                        else:
                            states = get_current()
                        
                        old_states = states
                        
                        print() # Print out new line for formatting
                        print('> ' + msg_content) # Print out user message
                        
                        # Automatically prints out response as it's written
                        result, states = await consumer(msg_content, states=states, function=set_typing, function_args=message)

                        # Purely debug
                        # print(states[0][0][0]) Prints out the lowest level array
                        # for state in states[0][0][0]: Prints out every entry in the lowest level array
                        #     print(state)

                        while result.startswith(' '):
                            result = result[1:]
                        
                        if result == '':
                            result = "..."
                        
                        await send_message(message, result)
                        
                        print() # Move cursor to next line after response
                        
                        log('\n> ' + msg_content + '\n' + result + '\n') # Log entire interaction
                        if autosave:
                            # Get the difference in the states
                            states_diff = []
                            for num in range(len(states)):
                                for num_two in range(len(states[num])):
                                    for num_three in range(len(states[num][num_two])):
                                        for num_four in range(len(states[num][num_two][num_three])):
                                            states_diff.append(old_states[num][num_two][num_three][num_four] - states[num][num_two][num_three][num_four])
                                        
                            add_states_to_queue(message.channel, states_diff)
                            write_state_queue()
                            # save_channel_states(message.channel) Old saving

                        if len(processing_users[message.author.id]) <= 1:
                            processing_users.pop(message.author.id, None)
                        else:
                            processing_users[message.author.id].remove(message.channel.id)
                    else:
                        await send_message(message, 'Your message is too long')
                else:
                    await send_message(message, 'Your message is empty')
            else:
                await send_message(message, 'Please wait for your response to be generated before sending more messages')

client.run('Token Goes Here', reconnect=True)
