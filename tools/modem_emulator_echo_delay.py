#!/usr/bin/env python3
"""
modem_emulator_echo_delay.py

Emula un modem seriale su COM2 (con fallback su loop://).
- Echo immediato dei caratteri ricevuti (comportamento tipico dei modem).
- Quando riceve una riga (terminata da CR o LF):
    * attende 3 secondi
    * se il comando è "ATI" → invia la risposta simulata
    * altrimenti → invia "ERROR\r\n"
"""

import time
import serial
from serial import serial_for_url

PORT = "COM2"
BAUDRATE = 9600
TIMEOUT = 0.1   # tempo massimo di attesa per byte singolo
WAIT_S = 0.5

ATI_RESPONSE = (
    "Manufacturer: INCORPORATED\r\n"
    "Model: A7600C\r\n"
    "Revision: A7600C_V1.0\r\n"
    "IMEI: 351602000330570\r\n"
    "+GCAP: +CGSM,+FCLASS,+DS\r\n\r\n"
    "OK\r\n"
)

def open_serial(port):
    try:
        ser = serial.Serial(
            port=port,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=TIMEOUT
        )
        print(f"Porta aperta: {port}")
        return ser
    except Exception as e:
        print(f"Impossibile aprire {port}: {e}")
        print("Uso fallback con 'loop://' per test (porta virtuale).")
        return serial_for_url('loop://', timeout=TIMEOUT)

def process_command(cmd_str, ser):
    """Gestisce un comando AT dopo una pausa di 3 secondi."""
    if not cmd_str:
        return
    print(f"Comando ricevuto: '{cmd_str}' — attendo {WAIT_S} secondi prima della risposta...")
    time.sleep(WAIT_S)
    if cmd_str.upper() == "ATI":
        ser.write(ATI_RESPONSE.encode())
        print("→ Risposta ATI inviata")
    else:
        ser.write(b"ERROR\r\n")
        print("→ Risposta ERROR inviata")

def main():
    ser = open_serial(PORT)
    buffer = bytearray()

    print(f"Emulatore seriale con echo e ritardo attivo ({WAIT_S} secondi).")
    print("In ascolto... (Ctrl-C per uscire)")

    try:
        while True:
            b = ser.read(1)
            if b:
                # Echo immediato del carattere ricevuto
                ser.write(b)
                buffer.extend(b)

                # Rileva fine riga (CR o LF)
                if b in (b'\r', b'\n'):
                    line = buffer.decode(errors='ignore').strip()
                    if line:
                        process_command(line, ser)
                    buffer.clear()
            else:
                time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nInterruzione utente. Chiusura...")
    finally:
        ser.close()
        print("Porta seriale chiusa.")

if __name__ == "__main__":
    main()
