"""
Assetto Corsa Time Saver File
Created by Ukato
Last Updated 14/06/2023
"""

import json
import os
from datetime import datetime

from PIL import Image, ImageFilter
from pytesseract import pytesseract


def get_time(img: Image) -> str | None:
    """
    Retrieves best track time from an image
    This function will return the time in string format to be stored
    If tesseract fails to recognise the time or if the image is not valid, this will return None

    :param img: Image to retrieve the time from
    :return: The best time in string format, None if it fails to do so
    """
    # Tesseract Custom Configuration
    custom_config = r'--oem 3 --psm 6'
    # oem 3 for more processing power, psm 6 for "assume a single uniform block of vertically aligned text of variable
    # sizes."

    # Define the dictionary and make tesseract expect to identify these words (1 means yes you should expect it)
    my_dict = {
        'Best': 1
    }
    custom_config += f" --user-words {','.join(my_dict.keys())}"
    custom_config += f" --user-patterns {','.join(my_dict.keys())}"

    # Locate engine
    pytesseract.tesseract_cmd = r'C:\Users\junis\AppData\Local\Tesseract-OCR\tesseract.exe'

    # dimensions
    width, height = img.size

    # Origin (0,0) is at the top left of the image
    # Top left coordinates of the image
    left = 0
    upper = 0
    # bottom right coordinates of the image
    right = width // 5
    lower = height // 2.5

    cropped_image = img.crop((left, upper, right, lower))

    # Image Processing:
    edited_image = cropped_image.convert("L")  # Convert to greyscale
    edited_image = edited_image.filter(ImageFilter.FIND_EDGES())  # Find Edges
    edited_image = edited_image.filter(ImageFilter.GaussianBlur(radius=0.5))  # Smooth out edges by blurring slightly

    # Get Text Detected in image
    text = pytesseract.image_to_string(edited_image, config=custom_config)

    text_list = text.split('\n')
    # Find the best time in the text
    for time in text_list:
        if "Best" in time:
            time_str = time.split(' ')
            best_index = int()
            for i in range(len(time_str)):  # Compare each item to find the word 'Best'
                if "Best" in time_str[i]:
                    best_index = i
                    break
            best_time = time_str[best_index + 1]
            return best_time

    return None


def store_time(time: str, track_name: str, name: str) -> bool:
    """
    Stores the stopwatch time into a json file
    This function will return a True/False value to indicate
    if the time was properly saved into its relevant file.

    :param time: Best Time in string format
    :param track_name:  The name of the track it was achieved on
    :param name: The name of the user who achieved the time
    :return: Boolean Value indicating success
    """
    # Open current Leaderboard
    track_name = track_name.lower()
    try:  # attempt to open existing file
        f = open(os.path.join("time folder", f"{track_name}.json"), "r")
    except FileNotFoundError:  # if file does not exist return false to indicate it failed
        return False

    # Load up the current Leaderboard for the given track
    f = open(os.path.join("time folder", f"{track_name}.json"), "r")
    current_leaderboard = json.load(f)
    f.close()

    # Add new time
    try:  # Only replace the current best time if the new time is faster
        if convert_str_to_time(current_leaderboard[f"{name}"]) >= convert_str_to_time(time):
            current_leaderboard[f"{name}"] = format_time_string(time)
    except KeyError:  # If best time does not exist, create it
        current_leaderboard[f"{name}"] = format_time_string(time)

    # Save the new leaderboard
    with open(os.path.join("time folder", f"{track_name}.json"), "w") as f:
        json.dump(current_leaderboard, f)

    return True


def show_leaderboard(track_name: str) -> list | None:
    """
    Sorts by time and returns the leaderboard for a given track
    :param track_name: The name of the track you want the leaderboard for
    :return: A list containing each user and their best times in order
    """
    try:  # attempt to open existing file
        f = open(os.path.join("time folder", f"{track_name}.json"), "r")
    except FileNotFoundError:
        return None
    current_leaderboard = json.load(f)

    leaderboard_converted = {key: value for key, value in
                             zip(current_leaderboard.keys(), map(convert_str_to_time, current_leaderboard.values()))}

    return_leaderboard = []
    for user, time in sorted(leaderboard_converted.items(), key=lambda x: x[1], reverse=False):
        time = time.strftime("%M:%S:%f").strip('0')
        return_leaderboard.append(f"{user}: {time}")

    for i in range(len(return_leaderboard)):
        return_leaderboard[i] = str(int(i + 1)) + '. ' + return_leaderboard[i]
    return return_leaderboard


def show_track_name_with_record() -> str:
    """
    Used to get the names of every single available track save in the folder
    :return: A string formatted with every track name on a separate line
    """
    files = os.listdir('time folder')
    ret_string = ''
    # iterate through the list of files and make it into one string
    for file in files:
        name = file[:-5]
        ret_string += f'{name.capitalize()} \n'
    return ret_string


def create_track(track_name: str) -> bool:
    """
    Creates a json file for a new track to store records on
    This function will return a True or False value to indicate if the file was created
    without any issues.
    :param track_name: The new track name
    :return: Boolean value to indicate success
    """
    # Create a json file in the time folder
    try:
        json_string = json.dumps({})
        with open(os.path.join("time folder", f"{track_name}.json"), "w") as f:
            f.write(json_string)
            f.close()
    except Exception as e:
        return False

    return True


def convert_str_to_time(str_time):
    """
    Converts a string containing a time into a date time datatype

    :param str_time: A string of a time in the format MIN:SEC:MILLISEC
    :return: Datetime value of the time record
    """
    # Converts the input string to date time format
    str_time = format_time_string(str_time)
    raw_time = datetime.strptime(str_time, "%M:%S:%f")
    res = raw_time.time()
    return res


def format_time_string(str_time: str) -> str:
    """
        Formats the string into the appropriate format
        This is for consistency as sometimes, the engine recognises ':' as another character

        :param str_time: A string of a time
        :return: Formatted string in format MIN:SEC:MILLISEC
        """
    # Converts the input string to date time format
    # Converts date time into a string
    str_time = str_time.replace('.', ':')
    str_time = str_time.strip(':.')
    return str_time


if __name__ == "__main__":
    time1 = '0:10:123'
    store_time(time1, 'test', 'test')
