import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

# Serial port settings
serial_port = 'COM8'  # Adjust as necessary
baud_rate = 115200

# Open serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=0.05)
ser.reset_input_buffer()  # Clear buffer to avoid lag

times = []
red_data = []
ir_data = []

fig, (ax_red, ax_ir) = plt.subplots(2,1,sharex=True)
line_red, = ax_red.plot([], [], label = 'Red', color = 'red', lw=2)
line_ir, = ax_ir.plot([],[], label="IR", color='blue',lw=2)

ax_red.set_ylabel('Red')
ax_red.set_title('Real-Time Red Sensor Readings')

ax_ir.set_ylabel('IR')
ax_ir.set_title('Real-Time IR Sensor Readings')

fig.suptitle('Real-Time MAX30102 Sensor Data')
ax_ir.set_xlabel('Time (s)')

start_time = time.time()

def init():
    line_red.set_data([], [])
    line_ir.set_data([], [])
    return line_red, line_ir

def update(frame):
    global times, red_data, ir_data
    current_time = time.time()-start_time

    # Read all available lines from the serial port
    while ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            parts = line.split(',')
            if len(parts) < 2 or '=' not in parts[0] or '=' not in parts[1]:
                continue

            red_val = float(parts[0].split('=')[1])
            ir_val = float(parts[1].split('=')[1])

            times.append(current_time)
            red_data.append(red_val)
            ir_data.append(ir_val)
        except Exception as e:
            print(f"Error parsing line: {line} Error: {e}")

    # Rolling Window
    window = 5
    while times and (current_time - times[0]) > window:
        times.pop(0)
        red_data.pop(0)
        ir_data.pop(0)
    
    line_red.set_data(times, red_data)
    line_ir.set_data(times, ir_data)

    # Scroll x-axis
    ax_red.set_xlim(max(0, current_time - window), current_time + 0.5)
    ax_ir.set_xlim(max(0, current_time - window), current_time + 0.5)
    #ax.relim()
    #ax.autoscale_view(scaley=True)
    """all_values = red_data + ir_data
    if all_values:
        ymin = min(all_values)
        ymax = max(all_values)
        margin = 0.1 * (ymax - ymin) if ymax != ymin else 100  # Add 10% margin or fallback
        ax.set_ylim(ymin - margin, ymax + margin)"""
    
    # Dynamic y-axis for red
    if red_data:
        red_min = min(red_data)
        red_max = max(red_data)
        margin = 0.1 * (red_max - red_min) if red_max != red_min else 100
        ax_red.set_ylim(red_min - margin, red_max + margin)
    
    if ir_data:
        ir_min = min(ir_data)
        ir_max = max(ir_data)
        margin = 0.1 * (ir_max - ir_min) if ir_max != ir_min else 100
        ax_ir.set_ylim(ir_min - margin, ir_max + margin)

    return line_red, line_ir

# Create animation (updates every 50ms)
ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=50)

# Show the plot
plt.show()

# Close serial port when plot is closed
ser.close()