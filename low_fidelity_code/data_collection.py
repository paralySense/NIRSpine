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

# Set up serial connection
serial_port = 'COM6'
baud_rate = 9600
ser = serial.Serial(serial_port, baud_rate, timeout=0.05)
ser.reset_input_buffer()    # Clear buffer to avoid lag

# Initialize lists to store data
time_window = 50   # Number of points to display
diode_data = [0] * time_window
time_points = np.arange(time_window)

# Set up figure and subplots
fig, (ax1) = plt.subplots(1, 1, figsize=(8,6))
fig.suptitle("Real time photodiode data")

# Line elements for each subplot
line1, = ax1.plot(time_points, diode_data, label="Photodiode", color='r')

# Formatting
ax1.set_xlim(0, time_window)
ax1.set_ylim(0,100)
ax1.legend()
ax1.grid()

# -----------------------------------------------------------------------------------------------

# Global flag to control recording
recording = False
csv_file = None
csv_writer = None

# Function to start recording data
def record_data():
    global recording, csv_file, csv_writer, latest_intensity
    intensity_buffer = []   # To store last 10 recordings (for smoothing average)

    while True:
        if recording and latest_intensity is not None:
            try:
                intensity_buffer.append(latest_intensity)

                if len(intensity_buffer) > 20:
                    intensity_buffer.pop(0)
                
                smoothed_buffer = sum(intensity_buffer)/len(intensity_buffer)

                timestamp = time.time()

                csv_writer.writerow([timestamp, smoothed_buffer])
                csv_file.flush()    # Ensure immediate write

            except Exception as e:
                print("Recording Error:", e)
        
        time.sleep(0.005) # Prevent cpu overuse

# Function to toggle recording on spacebar press
def toggle_record(event):
    global recording, csv_file, csv_writer, latest_intensity

    if recording:
        print("Stopping Recording")
        recording = False
        csv_file.close()
        print("Data saved.")

    else:
        print("Starting Recording")

        # Ensure folder exists
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
        csv_writer.writerow(["Time","NIR_Intensity"])

        print(f"Recording to {filename}")
        recording = True

# Attach spacebar event listener
keyboard.on_press_key('space', toggle_record)

# ----------------------------------------------------------------------------------

# Function to update plot
def update(frame): 
    global diode_data, latest_intensity

    if latest_intensity is not None:
        print(latest_intensity)
        diode_data.append(latest_intensity)

        if len(diode_data) >= time_window:
            diode_data.pop(0)
        
        # Apply moving average (over last 10 data points)?

        line1.set_ydata(diode_data)
    
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
    global latest_intensity
    while True:
        try:
            if ser.in_waiting > 0:  # Check if data is available before reading
                line = ser.readline().decode('utf-8').strip()
                if line.isdigit():
                    latest_intensity = int(line)  # Store the latest valid reading
                else:
                    print(f"Invalid data received: {line.encode()}")

        except Exception as e:
            print("Serial Read Error:", e)

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
    ani = animation.FuncAnimation(fig, update, interval=5, blit=False)
    plt.show()

    # Close serial port after the plot window is closed
    ser.close()

    # atexit.register(close_csv)