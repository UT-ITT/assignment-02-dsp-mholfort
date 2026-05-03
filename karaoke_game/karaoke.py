import sounddevice as sd
import numpy as np
import pyglet
from pyglet import window
import os


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

current_pitch = 0

notes = {"C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00}
song = ["E4", "E4", "F4", "G4", "G4", "F4", "E4", "D4",
        "C4", "C4", "D4", "E4", "E4", "D4", "D4",
        "E4", "E4", "F4", "G4", "G4", "F4", "E4", "D4",
        "C4", "C4", "D4", "E4", "E4", "C4", "C4"]

sung_note = ""
current_note = 0 
target_note = song[current_note]

note_timer = 0
BPM = 120
beat_duration = 60 / BPM
song_time = 0
last_note = -1

song_over = False

score = 0
matched_note = False

start_game = False

def audio_callback(indata, frames, time, status):
    global current_pitch

    if status:
        print(status)

    data = indata[:, 0]
    data = data * np.hanning(len(data))

    spectrum = np.abs(np.fft.fft(data))
    frequencies = np.fft.fftfreq(len(data), 1/RATE)
    
    mask = (frequencies >= 500) & (frequencies <= 4000)
    mask_spectrum = spectrum[mask]
    mask_frequencies = frequencies[mask]

    peak = np.argmax(mask_spectrum)
    pitch = mask_frequencies[peak]

    current_pitch = pitch

def play_note(note_name, duration):
    
    freq = notes[note_name]

    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    wave = 0.5 * np.sin(2 * np.pi * freq * t)

    fade_len = int(0.05 * sample_rate)

    wave[:fade_len] *= np.linspace(0, 1, fade_len)
    wave[-fade_len:] *= np.linspace(1, 0, fade_len)

    wave = wave.astype(np.float32)

    sd.play(wave, sample_rate)


def note_match(current_pitch, notes):
    global sung_note

    note_list = list(notes.items())
    smallest_diff = float("inf")
    
    for name, freq in note_list:
        diff = abs(current_pitch - freq)

        if diff < smallest_diff:
            smallest_diff = diff
            sung_note = name

    if smallest_diff <= 15:
        return sung_note, True
    else:
        return sung_note, False
    

def song_play(dt):
    global current_note, target_note, song_over, matched_note, score, song_time, beat_duration, last_note

    song_time += dt

    current_note = int(song_time/beat_duration)

    if current_note >= len(song):
        song_over = True
    else:
        target_note = song[current_note]

    if current_note != last_note:
        play_note(target_note, beat_duration)
        last_note = current_note

    if matched_note:
        score += 10

    matched_note = False


#pyglet
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

win = window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)
win.set_caption("Karaoke")


points = pyglet.text.Label('',
                          font_name='Bauhaus 93',
                          font_size=20,
                          color=(48, 201, 6),
                          x=20, y=570)

pitch = pyglet.text.Label('',
                          font_name='Bauhaus 93',
                          font_size=20,
                          color=(48, 201, 6),
                          x=275, y=WINDOW_HEIGHT/2,)

note = pyglet.text.Label('',
                          font_name='Bauhaus 93',
                          font_size=20,
                          color=(48, 201, 6),
                          x=275, y=WINDOW_HEIGHT/2-30,)

sing = pyglet.text.Label('',
                          font_name='Bauhaus 93',
                          font_size=30,
                          color=(48, 201, 6),
                          x=295, y=WINDOW_HEIGHT/2+80)

finish = pyglet.text.Label('Press R to restart',
                          font_name='Bauhaus 93',
                          font_size=30,
                          color=(48, 201, 6),
                          x=255, y=WINDOW_HEIGHT/2-100)

final = pyglet.text.Label('',
                          font_name='Bauhaus 93',
                          font_size=20,
                          color=(48, 201, 6),
                          x=320, y=WINDOW_HEIGHT/2,)

start = pyglet.text.Label('Press SPACE to start',
                          font_name='Bauhaus 93',
                          font_size=30,
                          color=(48, 201, 6),
                          x=250, y=WINDOW_HEIGHT/2-100,)
    
    

@win.event
def on_draw():
    global song_over
    win.clear()

    sing.draw()
    

    if start_game == False:
        start.draw()
    
    if song_over == True:
        finish.draw()
        final.draw()

    if song_over == False:
        pitch.draw()
        note.draw()
        points.draw()

def update(dt):
    global sung_note, score, matched_note, start_game

    sing.text = 'Test your voice'

    if start_game and not song_over:
        song_play(dt)

        sung_note, correct = note_match(current_pitch, notes)

        if sung_note == target_note and correct:
            matched_note = True

        sing.text = f'Sing: {target_note}'
        points.text = f'Score: {score}'
        pitch.text = f'Your Pitch: {current_pitch:.2f}'
        note.text = f'Your Note: {sung_note}'

    if song_over == True:
        sing.text = 'Game Over'
        final.text = f'Final Score: {score}'
   
    
def restart():
    global score, current_pitch, song_over, matched_note, start_game, sung_note, song_time, last_note
    score = 0
    song_over = False
    matched_note = False
    start_game = False
    sung_note = ""
    current_pitch = 0
    song_time = 0
    last_note = -1
    
    points.text = ''
    pitch.text = ''
    note.text = ''


@win.event
def on_key_press(symbol, modifiers):
    global start_game

    if symbol == pyglet.window.key.SPACE:
        start_game = True

    if symbol == pyglet.window.key.R:
        restart()

    if symbol == pyglet.window.key.Q:
        os._exit(0)


stream = sd.InputStream(
    device=input_device,
    channels=CHANNELS,
    samplerate=RATE,
    blocksize=CHUNK_SIZE,
    callback=audio_callback,
    latency='low'
)
stream.start()

pyglet.clock.schedule_interval(update, 1/10)

pyglet.app.run()
