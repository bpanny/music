import io
import random
import tempfile
import os
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename

# --- Import from your existing script ---
try:
    from modular_chord_generator import (
        PITCH_MAP, NOTE_NAMES, SCALES, DIATONIC_QUALITIES, CHORD_VOICINGS,
        get_diatonic_chords, get_chord_pitches
    )
    from modular_chord_generator import Note, Chord, Track, Composition, MidiExporter
except ImportError as e:
    print(f"Error importing from modular_chord_generator.py: {e}")
    exit()

app = Flask(__name__)

# --- App Configuration ---
TIME_SIGNATURE = (4, 4)
INSTRUMENT_PROGRAM = 50 
CHANNEL = 0
VOLUME = 90

### NEW ###
# This is the "brain" of the new feature.
# It defines what extensions are "allowed" for each base chord type.
# 'type': 'diatonic' (the base), 'compatible' (fits well), 'deviation' (color/tension)
CHORD_PALETTE_RULES = {
    'maj': [
        {'symbol_suffix': 'maj', 'type': 'diatonic'},
        {'symbol_suffix': 'maj7', 'type': 'compatible'},
        {'symbol_suffix': 'maj9', 'type': 'compatible'},
        {'symbol_suffix': 'add9', 'type': 'compatible'},
        {'symbol_suffix': 'maj13', 'type': 'compatible'},
        {'symbol_suffix': 'maj7#11', 'type': 'deviation'},
        {'symbol_suffix': 'sus2', 'type': 'deviation'},
        {'symbol_suffix': 'sus4', 'type': 'deviation'},
    ],
    'min': [
        {'symbol_suffix': 'min', 'type': 'diatonic'},
        {'symbol_suffix': 'min7', 'type': 'compatible'},
        {'symbol_suffix': 'min9', 'type': 'compatible'},
        {'symbol_suffix': 'min11', 'type': 'compatible'},
        {'symbol_suffix': 'min13', 'type': 'compatible'},
        {'symbol_suffix': 'min(add9)', 'type': 'compatible'},
    ],
    'dom7': [
        {'symbol_suffix': 'dom7', 'type': 'diatonic'},
        {'symbol_suffix': 'dom9', 'type': 'compatible'},
        {'symbol_suffix': 'dom13', 'type': 'compatible'},
        {'symbol_suffix': 'sus4', 'type': 'deviation'},
        {'symbol_suffix': 'dom7#9', 'type': 'deviation'}, # Hendrix
        {'symbol_suffix': 'dom7b9', 'type': 'deviation'},
    ],
    'dim': [
        {'symbol_suffix': 'dim', 'type': 'diatonic'},
        {'symbol_suffix': 'm7b5', 'type': 'compatible'}, # Half-diminished
        {'symbol_suffix': 'dim7', 'type': 'deviation'}, # Fully-diminished
    ],
    'm7b5': [ # Rule for the half-diminished 7th
        {'symbol_suffix': 'm7b5', 'type': 'diatonic'},
    ],
    'maj(aug)': [
        {'symbol_suffix': 'maj(aug)', 'type': 'diatonic'},
    ]
}


@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

### NEW: Smarter Endpoint ###
@app.route('/get-chord-palette')
def api_get_chord_palette():
    """
    Returns a structured list of chord options for each degree
    of a given key and scale.
    """
    key = request.args.get('key')
    scale = request.args.get('scale')
    
    if not key or not scale:
        return jsonify({"error": "Missing 'key' or 'scale' parameter"}), 400

    if scale not in SCALES or scale not in DIATONIC_QUALITIES:
         return jsonify({"error": f"Invalid scale type: {scale}"}), 400

    try:
        # 1. Get info from music theory definitions
        root_val = PITCH_MAP[key.upper()]
        intervals = SCALES[scale]
        qualities = DIATONIC_QUALITIES[scale] # e.g., ['maj', 'min', 'min', ...]
        
        palette = []
        for i in range(7):
            # 2. Get the root note name
            note_val = (root_val + intervals[i]) % 12
            root_name = NOTE_NAMES[note_val]
            
            # 3. Get the base diatonic quality (e.g., 'maj', 'min', 'dom7')
            base_quality = qualities[i]

            degree_info = {
                "degree": i + 1,
                "root": root_name,
                "base_quality": base_quality,
                "options": []
            }

            # 4. Get the expansion rules for this base quality
            rules = CHORD_PALETTE_RULES.get(base_quality, [
                {'symbol_suffix': base_quality, 'type': 'diatonic'}
            ])
            
            for rule in rules:
                # 5. Build the full chord symbol (e.g., "C" + "maj7" -> "Cmaj7")
                full_symbol = f"{root_name}{rule['symbol_suffix']}"
                
                # 6. Only add it if we have a voicing for it in the backend
                if rule['symbol_suffix'] in CHORD_VOICINGS:
                     degree_info['options'].append({
                        "symbol": full_symbol,
                        "type": rule['type']
                    })

            # Ensure at least the base chord is there if rules missed it
            base_chord_symbol = f"{root_name}{base_quality}"
            if not any(opt['symbol'] == base_chord_symbol for opt in degree_info['options']) \
               and base_quality in CHORD_VOICINGS:
                 degree_info['options'].insert(0, {
                     "symbol": base_chord_symbol,
                     "type": "diatonic"
                 })

            palette.append(degree_info)
            
        return jsonify(palette)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# This endpoint is no longer used by the new frontend,
# but we'll leave it in case you want to use it for something else.
@app.route('/get-diatonic-chords')
def api_get_diatonic_chords():
    key = request.args.get('key')
    scale = request.args.get('scale')
    if not key or not scale:
        return jsonify({"error": "Missing 'key' or 'scale' parameter"}), 400
    try:
        chords = get_diatonic_chords(key, scale)
        return jsonify(chords)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/generate-midi', methods=['POST'])
def api_generate_midi():
    """
    API endpoint to generate and return a MIDI file.
    (This function remains the same as the previous version)
    """
    try:
        song_data = request.json
        song_structure = song_data.get('structure')
        global_settings = song_data.get('settings')

        if not song_structure:
            return jsonify({"error": "No 'structure' data in request"}), 400

        song = Composition(
            title=global_settings.get('title', 'Generated Song'),
            tempo=int(global_settings.get('tempo', 120)),
            time_signature=TIME_SIGNATURE
        )
        
        chord_track = Track(
            name="Chord Progression",
            instrument_program=INSTRUMENT_PROGRAM,
            channel=CHANNEL,
            volume=VOLUME
        )
        
        current_time = 0.0
        base_octave = int(global_settings.get('baseOctave', 4))
        
        for part in song_structure:
            part_chord_symbols = []
            
            if 'progression_symbols' in part and part['progression_symbols']:
                part_chord_symbols = part['progression_symbols']
            elif 'progression_degrees' in part and part['progression_degrees']:
                diatonic_chords = get_diatonic_chords(part['key'], part['scale_type'])
                for degree in part['progression_degrees']:
                    degree_index = int(degree) - 1
                    if 0 <= degree_index < 7:
                        part_chord_symbols.append(diatonic_chords[degree_index])
            
            if not part_chord_symbols:
                continue

            num_loops = int(part.get('num_loops', 1))
            for _ in range(num_loops):
                for i, chord_symbol in enumerate(part_chord_symbols):
                    
                    if not part['rhythm_beats']: continue
                    duration = float(part['rhythm_beats'][i % len(part['rhythm_beats'])])
                    
                    if chord_symbol.upper() == "REST":
                        current_time += duration
                        continue
                    
                    if not part['inversions'] or not part['octave_pattern']:
                        inversion = 0
                        oct_offset = 0
                    else:
                        inversion = int(part['inversions'][i % len(part['inversions'])])
                        oct_offset = int(part['octave_pattern'][i % len(part['octave_pattern'])])
                    
                    pitches = get_chord_pitches(chord_symbol, base_octave, oct_offset, inversion)
                    
                    play_style = part.get('play_style', 'block')
                    
                    if play_style == 'arpeggio':
                        # (Add your arpeggio logic from main() here)
                        note_objects = [
                            Note(pitch=p, start_time=current_time, duration=duration * 0.9, velocity=85)
                            for p in pitches
                        ]
                        chord_track.add_element(Chord(notes=note_objects))
                    else: 
                        note_objects = [
                            Note(pitch=p, start_time=current_time, duration=duration * 0.9, velocity=85)
                            for p in pitches
                        ]
                        chord_track.add_element(Chord(notes=note_objects))
                    
                    current_time += duration

        song.add_track(chord_track)

        # --- Export to a temporary file ---
        exporter = MidiExporter(ticks_per_beat=480)
        temp_file_handle, temp_file_path = tempfile.mkstemp(suffix='.mid')
        os.close(temp_file_handle) 

        try:
            exporter.export(song, temp_file_path)
            with open(temp_file_path, 'rb') as f:
                file_buffer = io.BytesIO(f.read())
        except Exception as e:
            os.remove(temp_file_path)
            raise e
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        file_buffer.seek(0)
        
        return send_file(
            file_buffer,
            as_attachment=True,
            download_name=secure_filename(f"{global_settings.get('title', 'song')}.mid"),
            mimetype='audio/midi'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)