"""
Ukato's Time Saver Discord Bot
Created by Ukato
See README
"""

import discord
import requests

from timesaver import *


def create_token():
    """
    Checks and creates a json file to store the discord token

    Go to the Discord Developer Platform and create your own discord bot
    Create a token, copy and paste it into the terminal when the file runs.

    :return: None
    """
    if not os.path.isfile('./token.json'):
        print("You do not have a set Discord token")
        new_token = input("Copy and paste your token here: ")
        jsonContent = {
            "TOKEN": new_token
        }
        with open('token.json', 'w') as f:
            json.dump(jsonContent, f)


def run_discord_bot():  # Use the main file to run this function
    token_file = open("token.json")
    token_data = json.load(token_file)
    TOKEN = token_data["TOKEN"]
    token_file.close()

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    tree = discord.app_commands.CommandTree(client)
    ban_list = []

    @client.event
    async def on_ready():
        await tree.sync(guild=discord.Object(id=961085980050350100))
        print('Bot is now running')

    @tree.command(name="help", description="How to use the assetto corsa time saver")
    async def help_ac_command(interaction):
        # Sends the text file containing how to use the bot, as an embedded message
        with open(r'TrackTimeSaver.txt', 'r') as f:
            help_message = f.read()
        embed = discord.Embed(title='Bot Help', color=0xa80808)
        embed.add_field(name='Assetto Corsa Record Saver', value=help_message, inline=False)
        await interaction.response.send_message(embed=embed)

    @tree.command(name="showtrack", description="Shows all available tracks/maps with a leaderboard")
    async def show_track_command(interaction):
        # Sends an embedded message showing all the available tracks
        track_names = show_track_name_with_record()
        embed = discord.Embed(title="Tracks",
                              description="All Tracks with records submitted by the discord server",
                              color=0xa80808)
        embed.add_field(name="Track Names", value=track_names, inline=False)
        await interaction.response.send_message(embed=embed)

    @tree.command(name="showleaderboard", description="Shows the leaderboard for a given race track/map")
    async def show_leaderboard_command(interaction, track_name: str):
        # Shows the current leaderboard for a track specified in the message
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
        await interaction.response.send_message(embed=embed)

    @tree.command(name="createtrack", description="Creates a leaderboard for a given race track/map")
    async def create_track_command(interaction, track_name: str):
        # Automatically creates a new json file in the time folder for any new tracks
        result = create_track(track_name)

        # Success message
        if result is False:
            await interaction.response.send_message(f'Track could not be made')
        else:
            await interaction.response.send_message(f'Track "{track_name}" was created successfully')

    @tree.command(name="addtime", description="Manually add a time for a given race track/map")
    async def add_time_command(interaction, time: str, track_name: str):
        # Manually add a time to the leaderboard, incase the time cannot be recognised
        # Message pre-processing
        username = str(interaction.author).split('#')[0]
        user_message = time
        user_message = user_message.strip(' ')
        message_list = user_message.split(' ')

        # Checks time format
        if any(c.isalpha() for c in message_list[-1]) is True:
            await interaction.response.send_message(
                r"Syntax might be wrong, your time should be in the format MIN:SEC:MILLISECOND")

        # Adds the time to the leaderboard
        else:
            track_name = track_name.strip(" ")

            try:  # Validate the time added
                result = store_time(time, track_name, username)
            except ValueError:
                await interaction.response.send_message("Sorry, the time you submitted was incorrect")
                return

            # Success message
            if result is True:
                await interaction.response.send_message('Time submitted successfully')
            else:
                await interaction.response.send_message(
                    f'Time could not be submitted as the track "{track_name}" does not exist')

    @client.event
    async def on_message(message):
        # Prevents Bot from responding to itself
        if message.author == client.user:
            return

        # Message Author formatted as Username#1234
        username = str(message.author).split('#')[0]
        user_id = str(message.author).split('#')[1]  # Discord Username Update may make this redundant
        user_UID = message.author.id  # Unique ID for each user, this is not the 4 digit #hashtag
        user_message = str(message.content).lower()  # User message converted to lowercase for consistency

        # This is for users that are banned from using the bot
        # Enable Developer Mode, Right-Click on a user and save the User ID at the bottom
        if user_UID in ban_list:
            return

        # Retrieve Any Image Attachment
        user_attachment = None
        if len(message.attachments) > 0:
            user_attachment = message.attachments[0].url

        # Print out what the Bot sees
        channel = str(message.channel)
        print(f"{message.author}: '{user_message}' ({channel})")
        if user_attachment is not None:
            print(f'message was sent with attachment: {user_attachment}')

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

    # Run Bot Client
    try:
        client.run(TOKEN)
    except:
        print("An issue has occurred running the bot, Possible Issues are: "
              "\n Incorrect Token Format    -> Open token.json file and check if your token is correct"
              "\n Poor Wifi Connection      -> Check Wifi Strength, Try turning it off and on again")
