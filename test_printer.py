
import serial
import time

PORT = "/dev/ttyAMA0"  # Change to your GPIO UART device if different

try:
    with serial.Serial(
        port=PORT,
        baudrate=9600,
        timeout=2
    ) as printer:

        # Initialize printer
        printer.write(b'\x1b\x40')
        time.sleep(0.5)

        # Print test receipt
        printer.write(b'========================\n')
        printer.write(b'      HELLO WORLD!\n')
        printer.write(b'========================\n')
        printer.write(b'Raspberry Pi 5\n')
        printer.write(b'58mm Thermal Printer\n')
        printer.write(b'Test Print Successful!\n')
        printer.write(b'========================\n\n\n')

        printer.flush()

    print("Print command sent!")

except Exception as e:
    print("Error:", e)
