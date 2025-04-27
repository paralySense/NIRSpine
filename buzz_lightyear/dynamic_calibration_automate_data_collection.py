import serial
import keyboard
import csv
import time
import os
import sys

# Serial port settings
serial_port = 'COM8'  # Adjust as necessary
baud_rate = 115200

# Open serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=0.05)
ser.reset_input_buffer()  # Clear buffer to avoid lag

# Global control variables
recording = False
running = True
csv_file = None
csv_writer = None
temp_filename = None
last_space_press = 0  # To debounce spacebar input

def start_recording():
    global recording, csv_file, csv_writer, temp_filename
    print("Starting Recording")
    os.makedirs("recordings", exist_ok=True)
    temp_filename = os.path.join("recordings", f"{time.time()}.csv")
    csv_file = open(temp_filename, "w", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Time", "Red_light", "IR_light", "SpO2", "SpO2Valid"])
    csv_file.flush()
    
    recording = True

def stop_recording():
    global recording, running
    print("Stopping Recording")
    recording = False
    if csv_file:
        csv_file.flush()
        csv_file.close()

    custom_filename = input("Enter a name for your file (without extension): ")
    custom_filename = "".join(c if c.isalnum() or c in "_-" else "_" for c in custom_filename)

    if custom_filename:
        new_filepath = os.path.join("recordings", f"{custom_filename}.csv")
        os.rename(temp_filename, new_filepath)
        print(f"File saved as {custom_filename}.csv")
    else:
        print("Invalid filename! Keeping original timestamp-based name.")

    print("Serial port closing... Exiting...")
    running = False  # Stop the loop
    ser.close()


def handle_keyboard():
    global last_space_press
    if keyboard.is_pressed('space'):
        current_time = time.time()
        if current_time - last_space_press > 0.5:  # Prevent multiple triggers within 0.5s
            last_space_press = current_time
            if recording:
                stop_recording()
            else:
                start_recording()

def read_data():
    global recording, csv_writer, running

    if not running:
        return

    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8', errors='ignore').strip()

        # Validate and process data
        # if not line.replace(",", "").replace(".", "").replace("=", "").replace("-","").isalnum():
        """if not line.replace(",", "").replace(".", "").isdigit():
            print(f"Ignored non-numeric data: {line.encode()}")"""
        """if "=" not in line:
            print(f"Ignored non-numeric data: {line.encode()}")
            return"""
        if not line.replace(",", "").replace(".", "").isdigit():
            print(f"Ignored non-numeric data: {line.encode()}")       

        try:
            values = line.split(",")
            if len(values) == 4 and all("=" in v for v in values):
                red, ir, SpO2, SpO2valid = [float(v.split("=")[1]) for v in values]
                # red, ir, hr, HRvalid, SpO2, SpO2valid = map(float, values)
                # print(f"Data: {red}, {ir}, {hr}, {HRvalid}, {SpO2}, {SpO2valid}")
                if recording and csv_writer:
                    csv_writer.writerow([time.time(), red, ir, SpO2, SpO2valid])
                    csv_file.flush()
            else:
                print(f"Invalid data received: {line.encode()}")
        except ValueError as ve:
            print(f"Data conversion error {ve}")

def main_loop():
    print("Press SPACE to start/stop recording...")
    while running:
        handle_keyboard()
        read_data()
        time.sleep(0.01)  # Small delay to prevent excessive CPU usage
    print("Program terminated.")

if __name__ == "__main__":
    main_loop()