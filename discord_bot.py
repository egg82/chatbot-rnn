from chatbot import libchatbot
import discord
import asyncio
import os.path

try: # Unicode patch for Windows
    import win_unicode_console
    win_unicode_console.enable()
except:
    msg = "Please install the 'win_unicode_console' module."
    if os.name == 'nt': print(msg)

log_name = "Discord-Bot_Session.log"
log_file = open(log_name, "a", encoding="utf-8")

states_file = "general"
autosave = True
operators = ['']; # ID Tags
banned_users = ['']; # ID Tags
max_length = 500

print('Loading Chatbot-RNN...')
save, load, reset, consumer = libchatbot(max_length=max_length)
if os.path.exists(states_file + ".pkl") and os.path.isfile(states_file + ".pkl"):
    load(states_file)
    print('Loaded pre-existing Chatbot-RNN states.')
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

async def process_command(msg_content, message):
    global states_file, save, load, reset, consumer, autosave
    user_command_entered = False
    response = ""

    if message.author.id in banned_users:
        user_command_entered = True
        response = "Sorry, you have been banned."
    else:
        if message.author.id in operators:
            if msg_content.startswith('--reset'):
                user_command_entered = True
                reset()
                print()
                print("[Model state reset]")
                response = "Model state reset."
            elif msg_content.startswith('--save '):
                user_command_entered = True
                input_text = msg_content[len('--save '):]
                save(input_text)
                print()
                print("[Saved states to \"{}.pkl\"]".format(input_text))
                response = "Saved model state to \"{}.pkl\".".format(input_text)
            elif msg_content.startswith('--load '):
                user_command_entered = True
                input_text = msg_content[len('--load '):]
                load(input_text)
                print()
                print("[Loaded saved states from \"{}.pkl\"]".format(input_text))
                response = "Loaded saved model state from \"{}.pkl\".".format(input_text)
            elif msg_content.startswith('--autosave '):
                user_command_entered = True
                input_text = msg_content[len('--autosave '):]
                states_file = input_text
                print()
                print("[\"{}.pkl\" is now the default autosave destination]".format(input_text))
                response = "\"{}.pkl\" is now the default autosave destination.".format(input_text)
            elif msg_content.startswith('--autosaveon'):
                user_command_entered = True
                if not autosave:
                    autosave = True
                    print()
                    print("[Turned on autosaving (Currently saving to \"{}.pkl\")]".format(states_file))
                    response = "Turned on autosaving (Currently saving to \"{}.pkl\").".format(states_file)
                else:
                    response = "Autosaving is already on (Currently saving to \"{}.pkl\").".format(states_file)
            elif msg_content.startswith('--autosaveoff'):
                user_command_entered = True
                if autosave:
                    autosave = False
                    print()
                    print("[Turned off autosaving]")
                    response = "Turned off autosaving."
                else:
                    response = "Autosaving is already off."
        else:
            response = "Insufficient permissions."
    
    return user_command_entered, response

@client.event
async def on_message(message):
    global save, load, reset, consumer, states_file, autosave
    
    if message.content.startswith('>'):
        msg_content = '';
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
                    print()
                    print('> ' + msg_content + '')
                    log_file.write('\n> ' + msg_content + '')
                    result = consumer(msg_content)
                    await client.send_message(message.channel, result)
                    log_file.write('\n' + result)
                    log_file.write('\n')
                    if autosave:
                        save(states_file)
            else:
                await client.send_message(message.channel, 'Error: Message too long!')
        else:
            await client.send_message(message.channel, 'Error: Missing message!')

client.run('Token Goes Here')
