import numpy as np
import sounddevice as sd
import time
from pynput.keyboard import Key, Controller


CHUNK_SIZE = 1024 # Number of audio frames per buffer
RATE = 44100 # Audio sampling rate (HZ)
CHANNELS = 1 # Mono audio

""" print("Available input devices:\n")
devices = sd.query_devices()

input_devices = []
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        print(f"{i}: {dev['name']}")
        input_devices.append(i) """

# let user select audio device
input_device = 14 #int(input("\nSelect input device: "))


last_pitch = None
last_pitches = []
MAX_PITCHES = 8

trigger_time = 0
COOLDOWN = 0.8

keyboard = Controller()

def audio_callback(indata, frames, t, status):
    global last_pitch, last_pitches, trigger_time

    data = indata[:, 0]
    data = data * np.hanning(len(data))

    vol_strength = np.sqrt(np.mean(data**2))
    
    if vol_strength < 0.005:
        last_pitches.clear()
        return
    
    #FFT
    spectrum = np.abs(np.fft.rfft(data))
    frequencies = np.fft.rfftfreq(len(data), 1/RATE)

    #Range
    mask = (frequencies >= 600) & (frequencies <= 4000)
    mask_spectrum = spectrum[mask]
    mask_frequencies = frequencies[mask]

    if len(mask_spectrum) == 0:
        return

    #Pitch
    peak = np.argmax(mask_spectrum)
    pitch = mask_frequencies[peak]

    last_pitches.append(pitch)

    if len(last_pitches) > MAX_PITCHES:
        last_pitches.pop(0)

    if len(last_pitches) < MAX_PITCHES:
        return
        
    current_time = time.time() 

    if current_time - trigger_time < COOLDOWN:
        return
        
    #Up/down trend
    diffs = np.diff(last_pitches)
    avg = np.mean(diffs)

    total_change = last_pitches[-1] - last_pitches[0]

    pos_steps = np.sum(diffs > 0)
    neg_steps = np.sum(diffs < 0)

    needed_steps = 0.65 * len(diffs)

    if avg > 10 and total_change > 200 and pos_steps >= needed_steps:
        keyboard.press(Key.up)
        keyboard.release(Key.up)
        print("UP")
        trigger_time = current_time
    elif avg < -10 and total_change < -200 and neg_steps >= needed_steps:
        keyboard.press(Key.down)
        keyboard.release(Key.down)
        print("DOWN")
        trigger_time = current_time

    #print(round(pitch))


# open audio input stream
stream = sd.InputStream(
    device=input_device,
    channels=CHANNELS,
    samplerate=RATE,
    blocksize=CHUNK_SIZE,
    callback=audio_callback,
    latency='low'
)

# continously capture and plot audio signal
with stream:
    print("\nStreaming... (Ctrl+C to stop)")
    
    while True:
        time.sleep(0.1)
