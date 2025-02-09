# Data collection for first NIR in box system

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import keyboard
import csv
import threading
import time
import os
import atexit

latest_intensity = None     # Stores the most recent sensor reading
data_ready_event = threading.Event()
last_toggle_time = 0
start_time = 0
red = None
ir = None

# Set up serial connection
serial_port = 'COM6'
baud_rate = 9600
ser = serial.Serial(serial_port, baud_rate, timeout=0.05)
ser.reset_input_buffer()    # Clear buffer to avoid lag

# Initialize lists to store data
time_window = 20   # Number of points to display
# red_light_data = [0] * time_window
ir_light_data = [0] * time_window
time_points = np.arange(time_window)

# Set up figure and subplots
fig, (ax1) = plt.subplots(1, 1, figsize=(8,6))
fig.suptitle("Real time photodiode data")

# Line elements for each subplot
line1, = ax1.plot(time_points, ir_light_data, label="Photodiode Reading", color = 'r')

# Formatting
ax1.set_xlim(0, time_window)
ax1.set_ylim(0,300)
ax1.legend()
ax1.grid()

# -----------------------------------------------------------------------------------------------

# Global flag to control recording
recording = False
csv_file = None
csv_writer = None

# Function to start recording data
def record_data():
    global recording, csv_file, csv_writer, latest_intensity, red, ir
    # intensity_buffer = []   # To store last 10 recordings (for smoothing average)

    last_written_time = 0

    while True:

        data_ready_event.wait()

        if recording and ir is not None:
            timestamp = time.time()
            if timestamp - last_written_time > 0.01:
                csv_writer.writerow([timestamp, ir])
                csv_file.flush()
                # last_written_time = timestamp
        
        data_ready_event.clear()
        time.sleep(0.005) # Prevent cpu overuse

# Function to toggle recording on spacebar press
def toggle_record(event):
    global recording, csv_file, csv_writer, latest_intensity, last_toggle_time, start_time

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

    else:
        print("Starting Recording")

        # Ensure folder exists
        start_time = time.time()
        save_folder = "recordings"
        os.makedirs(save_folder, exist_ok = True)

        # Ask user for custom filename
        #custom_filename = input("Enter a name for your file (without extension): ")

        # Sanitize filename to avoid illegal characters
        # custom_filename = "".join(c if c.isalnum() or c in "_-" else "_" for c in custom_filename)
        time_filename = time.time()

        # Generate the full file path
        filename = os.path.join(save_folder, f"{time_filename}.csv") 

        csv_file = open(filename, "w", newline = "")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Time","Photodiode IR Reading"])

        print(f"Recording to {filename}")
        recording = True

# Attach spacebar event listener
keyboard.on_press_key('space', toggle_record)

# ----------------------------------------------------------------------------------

# Function to update plot
def update(frame): 
    global ir_light_data, latest_intensity, red, ir

    data_ready_event.wait()

    if ir is not None:
        ir_light_data.append(ir)
    
    if len(ir_light_data) >= time_window:
        ir_light_data.pop(0)
        
        # Apply moving average (over last 10 data points)?

        line1.set_ydata(ir_light_data)
    
    data_ready_event.clear()
    
    return line1,

'''def update(frame):
    global diode_data, latest_intensity

    try:
        line = ser.readline().decode('utf-8').strip()
        print(line)
        # values = line.split(",")
        # if len(line) == 1:        # Ensure correct data format
        if line.isdigit():
            # f1, f2, p = map(float, values)
            intensity = int(line)
            diode_data.append(intensity)

            # Keep only the last N data points
            # flow1_data = flow1_data[-time_window:]
            # flow2_data = flow2_data[-time_window:]
            # pressure_data = pressure_data[-time_window:]

            if len(diode_data) >= time_window:
                diode_data.pop(0)
                # flow1_data.pop(0)
                # flow2_data.pop(0)
                # pressure_data.pop(0)

            # Update the graph
            line1.set_ydata(diode_data)
        else:
            print(f"Invalid data recieved: {line}")
            return

    except Exception as e:
        print("Error:", e)
    
    return line1,'''

# Read data from serial monitor
def read_data():
    global red, ir
    while True:
        try:
            if ser.in_waiting > 0:  # Check if data is available before reading
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not line.replace(",", "").replace(".", "").isdigit():
                    print(f"Ignored non-numeric data: {line.encode()}")
                    continue  # Skip this iteration

                try:
                    ir = float(line)
                    print(f'data: {ir}')
                    '''values = line.split(",")
                    if len(line) == 1:
                        ir = map(float,values)
                        print(f"data: {ir}")'''

                    data_ready_event.set()
                    #else:
                        #print(f"Invalid data received: {line.encode()}")
                except ValueError as ve:
                    print(f"Data conversion error {ve}")
        except Exception as e:
            print("serial Read Error:", e)

        time.sleep(0.001)  # Lower sleep time for faster response

def close_csv():
    global csv_file
    if csv_file:
        csv_file.close()
        print("CSV file closed.")

if __name__ == "__main__":
    recording_thread = threading.Thread(target=record_data, daemon=True)
    recording_thread.start()

    serial_thread = threading.Thread(target=read_data, daemon=True)
    serial_thread.start()

    # Run the animation
    ani = animation.FuncAnimation(fig, update, interval=20, blit=False)
    plt.show()

    # Close serial port after the plot window is closed
    ser.close()

    atexit.register(close_csv)
