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
        get_diatonic_chords, get_chord_pitches,
        midi_to_note_name  # <-- IMPORT YOUR NEW HELPER
    )
    from modular_chord_generator import Note, Chord, Track, Composition, MidiExporter
except ImportError as e:
    print(f"Error importing from modular_chord_generator.py: {e}")
    exit()

app = Flask(__name__)

# ... (CHORD_PALETTE_RULES, @app.route('/'), @app.route('/get-chord-palette') are all unchanged) ...

# (Make sure CHORD_PALETTE_RULES and your /get-chord-palette endpoint are still here)
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
    return render_template('index.html')

@app.route('/get-chord-palette')
def api_get_chord_palette():
    # (This function is unchanged from the previous step)
    key = request.args.get('key')
    scale = request.args.get('scale')
    if not key or not scale: return jsonify({"error": "Missing 'key' or 'scale' parameter"}), 400
    if scale not in SCALES or scale not in DIATONIC_QUALITIES: return jsonify({"error": f"Invalid scale type: {scale}"}), 400
    try:
        root_val = PITCH_MAP[key.upper()]
        intervals = SCALES[scale]
        qualities = DIATONIC_QUALITIES[scale]
        palette = []
        for i in range(7):
            note_val = (root_val + intervals[i]) % 12
            root_name = NOTE_NAMES[note_val]
            base_quality = qualities[i]
            degree_info = { "degree": i + 1, "root": root_name, "base_quality": base_quality, "options": [] }
            rules = CHORD_PALETTE_RULES.get(base_quality, [{'symbol_suffix': base_quality, 'type': 'diatonic'}])
            for rule in rules:
                full_symbol = f"{root_name}{rule['symbol_suffix']}"
                if rule['symbol_suffix'] in CHORD_VOICINGS:
                     degree_info['options'].append({ "symbol": full_symbol, "type": rule['type'] })
            base_chord_symbol = f"{root_name}{base_quality}"
            if not any(opt['symbol'] == base_chord_symbol for opt in degree_info['options']) and base_quality in CHORD_VOICINGS:
                 degree_info['options'].insert(0, { "symbol": base_chord_symbol, "type": "diatonic" })
            palette.append(degree_info)
        return jsonify(palette)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


### --- ADD THIS NEW ENDPOINT --- ###
@app.route('/get-chord-data')
def api_get_chord_data():
    """
    Gets the raw pitch/note data for a chord symbol, inversion, and octave.
    """
    symbol = request.args.get('symbol')
    base_octave = int(request.args.get('base_octave', 4))
    inversion = int(request.args.get('inversion', 0))
    
    if not symbol:
        return jsonify({"error": "Missing 'symbol' parameter"}), 400
        
    try:
        # Get the raw MIDI pitches
        pitches = get_chord_pitches(
            chord_symbol=symbol,
            base_octave=base_octave,
            octave_offset=0, # Octave offset is now handled by note-level edits
            inversion=inversion
        )
        
        # Convert pitches to note names
        note_names = [midi_to_note_name(p) for p in pitches]
        
        return jsonify({
            "symbol": symbol,
            "pitches": pitches,
            "note_names": note_names,
            "inversion": inversion
        })
        
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


### --- COMPLETELY REPLACED FUNCTION --- ###
@app.route('/generate-midi', methods=['POST'])
def api_generate_midi():
    """
    Generates MIDI from a list of user-defined pitch-blocks.
    This is much simpler and more powerful than the old method.
    """
    try:
        song_data = request.json
        # This is the new, simpler data structure we expect
        progression_data = song_data.get('progression')
        global_settings = song_data.get('settings')

        if not progression_data:
            return jsonify({"error": "No 'progression' data in request"}), 400

        song = Composition(
            title=global_settings.get('title', 'Generated Song'),
            tempo=int(global_settings.get('tempo', 120)),
            time_signature=(4, 4) # Hard-coded for now
        )
        
        chord_track = Track(
            name="Chord Progression",
            instrument_program=int(global_settings.get('instrument', 50)),
            channel=0,
            volume=int(global_settings.get('volume', 90))
        )
        
        current_time = 0.0
        
        # Loop through the parts and their blocks
        for part in progression_data:
            num_loops = int(part.get('num_loops', 1))
            
            for _ in range(num_loops):
                # Loop through the actual chord blocks in this part
                for block in part.get('blocks', []):
                    
                    pitches = block.get('pitches', [])
                    duration = float(block.get('duration', 0))
                    
                    if not pitches or duration <= 0:
                        continue # Skip rests or empty blocks
                    
                    # Create the chord (as block notes)
                    note_objects = [
                        Note(
                            pitch=p,
                            start_time=current_time,
                            duration=duration * 0.9, # 90%
                            velocity=85
                        )
                        for p in pitches
                    ]
                    chord_track.add_element(Chord(notes=note_objects))
                    
                    # Advance time for the next block
                    current_time += duration

        song.add_track(chord_track)

        # --- Export to a temporary file (this logic is unchanged) ---
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