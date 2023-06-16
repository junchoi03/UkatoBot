"""
Ukato's Time Saver Discord Bot
Created by Ukato
Last Updated 14/06/2023
See README
"""

import discord
import requests

from timesaver import *


def run_discord_bot():  # Use the main file to run this function
    TOKEN = 'MTA0MDg2NjE4MTgyNzAwMjM3OA.GvAXJK.b4UQJcAbU0aNXYd17SE_oHs8e37X2ZDvC9GTi8'
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    ban_list = []

    @client.event
    async def on_ready():
        print(f'Bot is now running')

    @client.event
    async def on_message(message):
        # Prevents Bot from responding to itself
        if message.author == client.user:
            return

        # Message Author formatted as Username#1234
        username = str(message.author).split('#')[0]
        user_id = str(message.author).split('#')[1]  # Discord Username Update may make this redundant
        user_UID = message.author.id  # Unique ID for each user, this is not the 4 digit #
        user_message = str(message.content).lower()  # User message converted to lowercase for consistency

        # Retrieve Any Image Attachment
        user_attachment = None
        if len(message.attachments) > 0:
            user_attachment = message.attachments[0].url

        # Print out what the Bot sees
        channel = str(message.channel)
        print(f"{message.author}: '{user_message}' ({channel})")
        if user_attachment is not None:
            print(f'message was sent with attachment: {user_attachment}')

        # This is for users that are banned from using the bot
        # Enable Developer Mode, Right-Click on a user and save the User ID at the bottom
        if user_UID in ban_list:
            return

        # -------------------------------ASSETTO CORSA TIME SAVER-------------------------------------------
        if channel == 'timestable':  # Specified Channel will be used for the time saver function
            if user_attachment is not None:
                img = Image.open(requests.get(user_attachment, stream=True).raw)
                time = get_time(img)

                if len(user_message) == 0:  # Checks if user included a track name
                    await message.channel.send('Please include the track name with the screenshot')
                    return
                elif time is None:  # Checks if the time was retrieved from the image
                    await message.channel.send('Time could not be recognised, please add manually')
                    return

                # Stores the time in the appropriate json file with the right track name
                result = store_time(time, user_message, username)

                if result is False:  # checks if the time was stored properly
                    await message.channel.send(f'Track "{user_message}" does not exist')
                else:
                    await message.channel.send(f'{username} got a best time of {time} on the track "{user_message}"!')

            # Manually add a time to the leaderboard, incase the time cannot be recognised
            elif message.content.startswith('add time'):
                # Message pre-processing
                user_message = user_message[len('add time'):]
                user_message = user_message.strip(' ')
                message_list = user_message.split(' ')

                # Checks message layout
                if any(c.isalpha() for c in message_list[-1]) is True:
                    await message.channel.send(
                        r"Syntax might be wrong, to add a time manually type 'addtime [Track Name] [Track Time]'")

                # Adds the time to the leaderboard
                else:
                    time = message_list[-1]
                    message_list.remove(time)
                    track_name = " ".join(message_list)
                    track_name = track_name.strip(" ")

                    try:    # Validate the time added
                        result = store_time(time, track_name, username)
                    except ValueError:
                        await message.channel.send("Sorry, the time you submitted was incorrect")
                        return

                    # Success message
                    if result is True:
                        await message.channel.send('Time submitted successfully')
                    else:
                        await message.channel.send(
                            f'Time could not be submitted as the track "{track_name}" does not exist')

            # Automatically creates a new json file in the time folder for any new tracks
            elif message.content.startswith('create track'):
                message_string = user_message[len('create track'):]
                track_name = message_string.strip(' ')
                result = create_track(track_name)

                # Success message
                if result is False:
                    await message.channel.send(f'Track could not be made')
                else:
                    await message.channel.send(f'Track "{track_name}" was created successfully')

            # Shows the current leaderboard for a track specified in the message
            elif message.content.startswith('show leaderboard'):
                message_string = user_message[len('show leaderboard'):]
                track_name = message_string.strip(' ')
                leaderboard = show_leaderboard(track_name)
                result = ''
                if leaderboard is None:
                    result = "Track could not be found"
                else:
                    for i in range(len(leaderboard)):
                        if i >= 10:
                            result += "..."
                            break
                        record = leaderboard[i]
                        result += record + '\n'

                embed = discord.Embed(title='Leaderboard', description="Best times in format 'Min:Sec:Ms'",
                                      color=0xa80808)
                embed.add_field(name=track_name.capitalize(), value=result, inline=False)
                await message.channel.send(embed=embed)

            # Sends an embedded message showing all the available tracks
            elif user_message == 'show tracks':
                track_names = show_track_name_with_record()
                embed = discord.Embed(title="Tracks",
                                      description="All Tracks with records submitted by the discord server",
                                      color=0xa80808)
                embed.add_field(name="Track Names", value=track_names, inline=False)
                await message.channel.send(embed=embed)

            # Sends the text file containing how to use the bot, as an embedded message
            elif user_message == 'help':
                with open(r'TrackTimeSaver.txt', 'r') as f:
                    help_message = f.read()
                embed = discord.Embed(title='Bot Help', color=0xa80808)
                embed.add_field(name='Assetto Corsa Record Saver', value=help_message, inline=False)
                await message.channel.send(embed=embed)

    # Run Bot Client
    client.run(TOKEN)
