# Automate data collection for NIRS systems. This code was basically copied from MAX30102_data_collection.py and modified a bit.
# We have also taken out the ability to real-time graph in this code, since we don't think that's necessary for now.

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import keyboard
import csv
import threading
import time
import os
import sys
import shutil

data_ready_event = threading.Event()
last_toggle_time = 0
start_time = 0
red = None
ir = None
hr = None
HRvalid = None
SpO2 = None
SpO2valid = None
temp_filename = None

# Set up serial connection
serial_port = 'COM6'
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate, timeout=0.05)
ser.reset_input_buffer()    # Clear buffer to avoid lag

# Global flag to control recording
recording = False
csv_file = None
csv_writer = None

# Function to start recording data
def record_data():
    """
    Continuously writes sensor data to a CSV file while recording is active.

    This function runs in a background thread and writes time-stamped sensor readings 
    (red light, IR light, heart rate, and SpO2) to an open CSV file. It ensures that
    data is written at a controlled rate to avoid excessive CPU usage.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    global recording, csv_file, csv_writer, red, ir, hr, HRvalid, SpO2, SpO2valid

    last_written_time = 0

    while True:

        data_ready_event.wait()

        if recording:
            timestamp = time.time()
            if timestamp - last_written_time > 0.01:
                
                csv_writer.writerow([timestamp, red, ir, hr, HRvalid, SpO2, SpO2valid])
                csv_file.flush()
        
        data_ready_event.clear()
        time.sleep(0.005) # Prevent cpu overuse

# Function to toggle recording on spacebar press
def toggle_record(event):
    """
    Starts or stops data recording when a spacebar is pressed.

    If recording is not active, upon spacebar press this function initializes a new CSV file
    and starts logging sensor data. If recording is active, upon spacebar press it stops logging
    and prompts the user to enter a custom filename, renames the file to that name, and exits the program.

    Parameters
    ----------
    event : keyboard.KeyboardEvent
        The keyboard event triggered by pressing the spacebar.

    Returns
    -------
    None

    """
    global recording, csv_file, csv_writer, last_toggle_time, start_time, temp_filename

    current_time = time.time()
    if current_time - last_toggle_time < 0.5:   # Prevent multiple triggers within 0.5 seconds
        return  # Ignore this trigger
    
    last_toggle_time = current_time

    if recording:
        print("Stopping Recording")
        recording = False
        csv_file.close()
        csv_file = None
        print("Data saved.")

        custom_filename = input("Enter a name for your file (without extension): ")

        # Sanitize filename to avoid illegal characters
        custom_filename = "".join(c if c.isalnum() or c in "_-" else "_" for c in custom_filename)

        # Ensure the filename is not empty
        if not custom_filename:
            print("Invalid filename! Keeping the original timestamp-based name!")
        else:
            new_filepath = os.path.join("recordings", f"{custom_filename}.csv")
            old_filepath = os.path.join("recordings", f"{temp_filename}.csv")
        
            try:
                shutil.move(old_filepath, new_filepath)
                print(f"file renamed to {custom_filename}")
            except Exception as e:
                print(f"Error renaming file: {e}")
        
        # After renaming the file, close the program
        print("Exiting program...")

        if ser.is_open:
            ser.close()
            print("Serial port closed")
        
        close_csv()
        
        sys.exit(0)  # Immediately terminates the program

    else:
        print("Starting Recording")

        # Ensure folder exists
        start_time = time.time()
        save_folder = "recordings"
        os.makedirs(save_folder, exist_ok = True)

        temp_filename = str(time.time())

        # Generate the full file path
        filepath = os.path.join(save_folder, f"{temp_filename}.csv") 

        csv_file = open(filepath, "w", newline = "")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Time","Red_light","IR light", "HR", "HRvalid", "SPO2", "SPO2Valid"])

        print("Recording data")
        recording = True

# Attach spacebar event listener
keyboard.on_press_key('space', toggle_record)

# Read data from serial monitor
def read_data():
    """
    Reads and processes incoming data from the serial port.

    This function continuously monitors the serial port for incoming data. It
    reads sensor values, filters out invalid data, and updates global variables.
    If valid data is received, it sets an event flag to signal availability.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    global red, ir, hr, HRvalid, SpO2, SpO2valid
    while True:
        try:
            if ser.in_waiting > 0:  # Check if data is available before reading
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not line.replace(",", "").replace(".", "").isdigit():
                    print(f"Ignored non-numeric data: {line.encode()}")
                    continue  # Skip this iteration

                try:
                    values = line.split(",")
                    if len(values) == 6:
                        red, ir, hr, HRvalid, SpO2, SpO2valid = map(float,values) # modular
                        print(f"data: {red}, {ir}, {hr}, {HRvalid}, {SpO2}, {SpO2valid}") # modular

                        data_ready_event.set()
                    else:
                        print(f"Invalid data received: {line.encode()}")
                except ValueError as ve:
                    print(f"Data conversion error {ve}")
        except Exception as e:
            print("serial Read Error:", e)

        time.sleep(0.001)  # Lower sleep time for faster response

def close_csv():
    """
    Closes the currently open CSV file.

    Ensures that all buffered data is written to disk before closing the file.
    Prevents data corruption or loss in case of an unexpected termination.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    global csv_file
    if csv_file:
        csv_file.close()
        print("CSV file closed.")

if __name__ == "__main__":
    recording_thread = threading.Thread(target=record_data, daemon=True)
    recording_thread.start()

    serial_thread = threading.Thread(target=read_data, daemon=True)
    serial_thread.start()
