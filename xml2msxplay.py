# -*- coding: utf-8 -*-
"""
Utility to convert .musicxml files generated from TuxGuitar into .bas format for running on MSX systems.
"""

import xml.etree.ElementTree as ET
import sys
import os

DURATION_MAP = {
    "whole": 1,
    "half": 2,
    "quarter": 4,
    "eighth": 8,
    "16th": 16,
    "32nd": 32,
    "64th": 64,
}

ALTER_MAP = {1: "#", -1: "-"}

def parse_musicxml(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    measures = []
    tempos = []

    repeat_start_index = None
    all_measures = root.findall(".//measure")

    for measure in all_measures:
        measure_notes = []
        chord_buffer = []

        tempo_this_measure = None
        direction = measure.find("direction/direction-type/metronome")
        if direction is not None:
            per_min = direction.find("per-minute")
            if per_min is not None:
                tempo_this_measure = int(per_min.text)

        for note in measure.findall("note"):
            staff_el = note.find("staff")
            if staff_el is not None and staff_el.text != "1":
                continue

            if note.find("rest") is not None:
                duration_type = note.find("type")
                duration = DURATION_MAP.get(duration_type.text, 4) if duration_type is not None else 4
                has_dot = note.find("dot") is not None
                measure_notes.append(("R", duration, 0, None, False, has_dot))
                continue

            pitch = note.find("pitch")
            if pitch is None:
                continue
            step = pitch.find("step").text
            octave = int(pitch.find("octave").text)
            alter_el = pitch.find("alter")
            alter = int(alter_el.text) if alter_el is not None else 0
            note_type_el = note.find("type")
            duration = DURATION_MAP.get(note_type_el.text, 4) if note_type_el is not None else 4
            has_dot = note.find("dot") is not None
            is_chord = note.find("chord") is not None

            is_triplet = False
            time_mod = note.find("time-modification")
            if time_mod is not None:
                actual = time_mod.find("actual-notes")
                normal = time_mod.find("normal-notes")
                if actual is not None and normal is not None:
                    try:
                        if int(actual.text) == 3 and int(normal.text) == 2:
                            is_triplet = True
                    except ValueError:
                        pass

            if is_chord:
                chord_buffer.append((step, duration, alter, octave, is_triplet, has_dot))
            else:
                if chord_buffer:
                    chord_buffer.append((step, duration, alter, octave, is_triplet, has_dot))
                    lowest = min(chord_buffer, key=lambda n: (n[3], n[0]))
                    measure_notes.append(lowest)
                    chord_buffer.clear()
                else:
                    measure_notes.append((step, duration, alter, octave, is_triplet, has_dot))

        if chord_buffer:
            lowest = min(chord_buffer, key=lambda n: (n[3], n[0]))
            measure_notes.append(lowest)

        if measure_notes:
            measures.append(measure_notes)
            tempos.append(tempo_this_measure)

    return measures, tempos


def convert_measure_to_play(measure_notes, tempo=120):
    play_str = ""
    current_octave = None
    current_tempo = tempo

    for idx, note in enumerate(measure_notes):
        step, duration, alter, octave, is_triplet, has_dot = note

        tempo_to_use = int(tempo * 1.5) if is_triplet else tempo
        if tempo_to_use != current_tempo:
            play_str += f'T{tempo_to_use}'
            current_tempo = tempo_to_use

        if step == "R":
            play_str += f'R{duration}'
            if has_dot:
                play_str += '.'
            continue

        if current_octave != octave:
            play_str += f'O{octave}'
            current_octave = octave

        note_symbol = step
        if alter in ALTER_MAP:
            note_symbol += ALTER_MAP[alter]
        note_symbol += str(duration)
        if has_dot:
            note_symbol += '.'

        play_str += note_symbol

        next_is_triplet = False
        if idx + 1 < len(measure_notes):
            next_is_triplet = measure_notes[idx + 1][4]
        if is_triplet and not next_is_triplet:
            play_str += f'T{tempo}'
            current_tempo = tempo

    if not play_str.startswith("T"):
        play_str = f'T{tempo}' + play_str

    return play_str


def main():
    if len(sys.argv) < 2:
        print("Usage: python xml2msxplay.py file.musicxml")
        sys.exit(1)

    filename = sys.argv[1]
    tempo = int(sys.argv[2]) if len(sys.argv) > 2 else 120

    measures, tempos = parse_musicxml(filename)

    base_name = os.path.splitext(os.path.basename(filename))[0]
    play_file = base_name + ".bas"

    with open(play_file, "w", encoding="utf-8") as f:
        line_number = 10
        current_tempo = tempo
        for i, measure in enumerate(measures):
            if tempos[i] is not None:
                current_tempo = tempos[i]
            play_cmd = convert_measure_to_play(measure, current_tempo)
            f.write(f'{line_number} PLAY "{play_cmd}"\n')
            line_number += 10

    print(f"File {play_file} generated successfully!")
    input("Press ENTER to exit...")


if __name__ == "__main__":
    main()
