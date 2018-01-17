from chatbot import libchatbot
import discord
import asyncio
import os

try: # Unicode patch for Windows
    import win_unicode_console
    win_unicode_console.enable()
except:
    msg = "Please install the 'win_unicode_console' module."
    if os.name == 'nt': print(msg)

log_name = "Discord-Bot_Session.log"
log_file = open(log_name, "a", encoding="utf-8")

states_main = "states"
states_folder = states_main + "/" + "server_states"
states_folder_dm = states_main + "/" + "dm_states"

autosave = True
autoload = True
operators = ['']; # ID Tags
banned_users = ['']; # ID Tags
max_length = 500

print('Loading Chatbot-RNN...')
save, load, reset, consumer = libchatbot(max_length=max_length)
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

async def load_channel_states(channel):
    global states_folder, states_folder_dm, load, reset

    await make_folders()
    
    states_file = await get_states_file(channel)
        
    if os.path.exists(states_file + ".pkl") and os.path.isfile(states_file + ".pkl"):
        load(states_file)
    else:
        reset()

async def make_folders():
    if not os.path.exists(states_folder):
        os.makedirs(states_folder)

    if not os.path.exists(states_folder_dm):
        os.makedirs(states_folder_dm)

async def get_states_file(channel):
    if channel.is_private:
        states_file = states_folder_dm + "/" + channel.id
    else:
        states_file = states_folder + "/" + channel.id

    return states_file

async def save_channel_states(channel):
    global states_folder, states_folder_dm, save

    await make_folders()

    states_file = await get_states_file(channel)
    
    save(states_file)

async def process_command(msg_content, message):
    global save, load, reset, consumer, autosave
    user_command_entered = False
    response = ""

    if message.author.id in banned_users and not message.channel.is_private:
        user_command_entered = True
        response = "Sorry, you have been banned."
    else:
        # Operators and DMs can use these commands
        if msg_content.startswith('--reset'):
            user_command_entered = True
            if message.author.id in operators or message.channel.is_private:
                reset()
                await save_channel_states(message.channel)
                print()
                print("[Model state reset]")
                response = "Model state reset."
            else:
                response = "Insufficient permissions."
                
        # Operators can use these commands
        elif msg_content.startswith('--resetbasic'):
            user_command_entered = True
            if message.author.id in operators:
                reset()
                print()
                print("[Model state reset]")
                response = "Model state reset."
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
    
    return user_command_entered, response

@client.event
async def on_message(message):
    global save, load, reset, consumer, states_file, autosave
    
    if (message.content.startswith('>') or message.channel.is_private) and not message.author.bot:
        msg_content = message.content
        if message.content.startswith('> '):
            msg_content = message.content[len('> '):]
        elif message.content.startswith('>'):
            msg_content = message.content[len('>'):]
        
        await client.send_typing(message.channel)
        
        if not msg_content == '':
            if not len(msg_content) > max_length:
                user_command_entered, response = await process_command(msg_content, message)

                if user_command_entered:
                    await client.send_message(message.channel, response)
                else:
                    if autoload:
                        await load_channel_states(message.channel)
                    print()
                    print('> ' + msg_content + '')
                    log_file.write('\n> ' + msg_content + '')
                    result = consumer(msg_content)
                    await client.send_message(message.channel, result)
                    log_file.write('\n' + result)
                    log_file.write('\n')
                    if autosave:
                        await save_channel_states(message.channel)
            else:
                await client.send_message(message.channel, 'Error: Message too long!')
        else:
            await client.send_message(message.channel, 'Error: Missing message!')

client.run('Token Goes Here')
