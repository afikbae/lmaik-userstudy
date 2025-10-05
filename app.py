# app.py

from flask import Flask, render_template, request, redirect, url_for, session, abort, send_file
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
# This secret key is crucial for session management. Change it to something random and secret.
app.secret_key = 'your_super_secret_key_for_user_study'

# --- Configuration ---
QUESTIONS = [
    "Which motion appears more extraverted, enthusiastic?",
    "Which motion appears more critical, quarrelsome?",
    "Which motion appears more dependable, self-disciplined?",
    "Which motion appears more anxious, easily upset?",
    "Which motion appears more open to new experiences, complex?",
    "Which motion appears more reserved, quiet?",
    "Which motion appears more sympathetic, warm?",
    "Which motion appears more disorganized, careless?",
    "Which motion appears more calm, emotionally stable?",
    "Which motion appears more conventional, uncreative?",
    "Which motion appears happier?",
    "Which motion appears sadder?",
    "Which motion appears more afraid?",
    "Which motion appears more disgusted?",
    "Which motion appears angrier?",
    "Which motion appears more surprised?",
    "Which motion appears more human-like, natural?",
    "Rate the human-likeness (realism) of the motion on the left (1: poor, 5: excellent)?",
    "Rate the human-likeness (realism) of the motion on the right (1: poor, 5: excellent)?",
]

# Define the pairs of motions, now grouped into categories (parts).
TRIAL_CATEGORIES = [
    [
        ('walk-low-weight.bvh', 'walk-high-weight.bvh'),
        ('wave-low-weight.bvh', 'wave-high-weight.bvh'),
        ('sit-low-weight.bvh', 'sit-high-weight.bvh'),
        ('put-low-weight.bvh', 'put-high-weight.bvh'),
    ],
    [
        ('walk-low-space.bvh', 'walk-high-space.bvh'),
        ('wave-low-space.bvh', 'wave-high-space.bvh'),
        ('sit-low-space.bvh', 'sit-high-space.bvh'),
        ('put-low-space.bvh', 'put-high-space.bvh'),
    ],
    [
        ('walk-low-time.bvh', 'walk-high-time.bvh'),
        ('wave-low-time.bvh', 'wave-high-time.bvh'),
        ('sit-low-time.bvh', 'sit-high-time.bvh'),
        ('put-low-time.bvh', 'put-high-time.bvh'),
    ],
    [
        ('walk-low-flow.bvh', 'walk-high-flow.bvh'),
        ('wave-low-flow.bvh', 'wave-high-flow.bvh'),
        ('sit-low-flow.bvh', 'sit-high-flow.bvh'),
        ('put-low-flow.bvh', 'put-high-flow.bvh'),
    ],
]

# Flatten all pairs into a single list for all participants to see all 16 pairs
ALL_PAIRS = []
for category in TRIAL_CATEGORIES:
    ALL_PAIRS.extend(category)

TOTAL_TRIALS = len(ALL_PAIRS)
RESULTS_FILE = os.path.join('results', 'study_results.csv')

# Ensure the results directory exists
os.makedirs('results', exist_ok=True)

# --- Routes ---

# <-- CHANGED: The root route '/' now handles both GET and POST requests.
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prolific_id = request.form.get('prolific_id')
        if not prolific_id:
            return render_template('login.html', error="Prolific ID cannot be empty.")

        session['prolific_id'] = prolific_id
        session['current_trial'] = 1 # Start with the first trial

        # Randomize the order of all pairs for this participant
        session['trial_order'] = random.sample(range(len(ALL_PAIRS)), len(ALL_PAIRS))

        return redirect(url_for('run_trial', trial_num=1))

    # On GET, just show the login page
    return render_template('login.html')

# <-- REMOVED: The old @app.route('/userstudy') function is gone.
#     The logic has been merged into the index() function above.


@app.route('/trial/<int:trial_num>', methods=['GET', 'POST'])
def run_trial(trial_num):
    # Security checks: ensure user has a session and is on the correct trial
    if 'prolific_id' not in session:
        # <-- CHANGED: Redirect to 'index' instead of 'user_study'
        return redirect(url_for('index'))
    if trial_num != session.get('current_trial'):
        # Prevent users from skipping trials or going back
        return redirect(url_for('run_trial', trial_num=session['current_trial']))

    # --- POST: User has submitted the form ---
    if request.method == 'POST':
        # Calculate time taken for the trial
        time_taken = 'N/A'
        if 'trial_start_time' in session:
            start_time = datetime.fromisoformat(session['trial_start_time'])
            end_time = datetime.now()
            time_taken = round((end_time - start_time).total_seconds(), 2)

        # Construct the 'R' string as per Realism Personality.html format
        # Map string choices to numerical values (0, 1, 2)
        choice_mapping = {
            'Left': 0,
            'Equal': 1,
            'Right': 2,
            'N/A': -1 # Should not happen due to 'required' attribute
        }
        answers_numerical = {}
        for i in range(1, 20):
            form_value = request.form.get(f'q{i}', 'N/A')
            if i <= 17:
                answers_numerical[f'q{i}'] = choice_mapping.get(form_value, -1)
            else:
                # For rating questions (18, 19), store the rating value directly
                try:
                    answers_numerical[f'q{i}'] = int(form_value) if form_value != 'N/A' else -1
                except ValueError:
                    answers_numerical[f'q{i}'] = -1
        
        # Construct the 'R' string as per Realism Personality.html format
        choices_string = ",".join(str(answers_numerical[f'q{i}']) for i in range(1, 20))
        
        # Convert is_reversed boolean to 0 or 1
        is_reversed_int = 1 if session.get('is_reversed', False) else 0

        r_string = (
            f"modNo:{session.get('current_mod_no', 'N/A')}"
            f"#buttonChoices:{choices_string}"
            f"#time:{time_taken}"
            f"#isreverse:{is_reversed_int}"
        )

        row = {
            'PID': session['prolific_id'],
            'SNO': session.get('current_sno', trial_num), # SNO is the actual category index (randomized)
            'R': r_string
        }
        
        # Write to CSV
        file_exists = os.path.isfile(RESULTS_FILE)
        with open(RESULTS_FILE, 'a', newline='') as csvfile:
            fieldnames = row.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        
        # --- Move to the next trial ---
        session['current_trial'] += 1
        return redirect(url_for('run_trial', trial_num=session['current_trial']))

    # --- GET: Display the trial page ---
    if trial_num > TOTAL_TRIALS:
        return redirect(url_for('complete'))

    # Store trial start time in session
    session['trial_start_time'] = datetime.now().isoformat()

    # Get the randomized trial order for this participant
    trial_order = session.get('trial_order')
    if not trial_order:
        # Fallback if session was lost - randomize again
        trial_order = random.sample(range(len(ALL_PAIRS)), len(ALL_PAIRS))
        session['trial_order'] = trial_order

    # Get the actual pair index for this trial based on the randomized order
    pair_index = trial_order[trial_num - 1]
    motion_pair_for_trial = ALL_PAIRS[pair_index]

    # Determine which category and mod_no this pair belongs to for recording purposes
    category_index = pair_index // 4  # 0-3
    mod_no = pair_index % 4  # 0-3

    # Store the actual SNO (category index + 1 for 1-based indexing) for recording
    session['current_sno'] = category_index + 1
    session['current_mod_no'] = mod_no

    # Randomly decide whether to swap the motions and store the decision
    motion_left, motion_right = motion_pair_for_trial
    is_reversed = random.choice([True, False])
    session['is_reversed'] = is_reversed
    if is_reversed:
        motion_left, motion_right = motion_right, motion_left
    
    # Store the actual motions shown in the session to ensure we save the correct data on POST
    session['motion_left'] = motion_left
    session['motion_right'] = motion_right

    return render_template(
        'trial.html',
        trial_num=trial_num,
        total_trials=TOTAL_TRIALS,
        motion_left=motion_left,
        motion_right=motion_right,
        questions=QUESTIONS,
        mod_no=mod_no
    )

@app.route('/complete')
def complete():
    # A simple "Thank You" page
    prolific_id = session.get('prolific_id', 'Participant')
    
    # Clear the session so they can't go back
    session.clear() 
    
    return render_template('complete.html', prolific_id=prolific_id)


@app.route('/results')
def show_results():
    results = []
    header = []
    if os.path.isfile(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', newline='') as csvfile:
            try:
                reader = csv.reader(csvfile)
                header = next(reader)
                results = list(reader)
            except StopIteration:
                # Handle empty file
                pass
    return render_template('results.html', header=header, results=results)


@app.route('/download_csv')
def download_csv():
    try:
        return send_file(
            RESULTS_FILE,
            mimetype='text/csv',
            as_attachment=True,
            download_name='study_results.csv'
        )
    except FileNotFoundError:
        abort(404)


@app.route('/bvh_pairs')
def show_bvh_pairs():
    return render_template('bvh_pairs.html', trial_categories=TRIAL_CATEGORIES)


@app.route('/mpjpe')
def show_mpjpe():
    return render_template('mpjpe.html', trial_categories=TRIAL_CATEGORIES)


@app.route('/test_mpjpe')
def test_mpjpe():
    """Test endpoint to calculate MPJPE using Python backend"""
    from bvh_parser import calculate_mpjpe
    import os
    from flask import jsonify

    # Test with first pair from each category
    test_pairs = [
        ('walk-low-weight.bvh', 'walk-high-weight.bvh'),
        ('walk-low-space.bvh', 'walk-high-space.bvh'),
        ('walk-low-time.bvh', 'walk-high-time.bvh'),
        ('walk-low-flow.bvh', 'walk-high-flow.bvh'),
    ]

    results = []

    for left, right in test_pairs:
        left_path = os.path.join('static', 'bvh', left)
        right_path = os.path.join('static', 'bvh', right)

        try:
            result = calculate_mpjpe(left_path, right_path)
            results.append({
                'pair': f"{left} vs {right}",
                'mpjpe': round(result['mpjpe'], 4),
                'num_frames': result['num_frames'],
                'num_joints': result['num_joints'],
                'duration': round(result['duration'], 2),
                'min_error': round(result['min_error'], 4),
                'max_error': round(result['max_error'], 4),
                'first_frame_error': round(result['frame_errors'][0], 4) if result['frame_errors'] else 0,
                'last_frame_error': round(result['frame_errors'][-1], 4) if result['frame_errors'] else 0,
            })
        except Exception as e:
            results.append({
                'pair': f"{left} vs {right}",
                'error': str(e)
            })

    return jsonify(results)


@app.route('/test_mpjpe_identical')
def test_mpjpe_identical():
    """Test MPJPE with identical files (should return ~0)"""
    from bvh_parser import calculate_mpjpe
    import os
    from flask import jsonify

    # Test with same file compared to itself
    test_files = [
        'walk-low-weight.bvh',
        'wave-high-space.bvh',
        'sit-low-time.bvh',
    ]

    results = []

    for filename in test_files:
        filepath = os.path.join('static', 'bvh', filename)

        try:
            result = calculate_mpjpe(filepath, filepath)
            results.append({
                'file': filename,
                'mpjpe': round(result['mpjpe'], 10),  # More precision for near-zero values
                'num_frames': result['num_frames'],
                'num_joints': result['num_joints'],
                'max_error': round(result['max_error'], 10),
                'note': 'PASS - Near zero' if result['mpjpe'] < 0.001 else 'FAIL - Should be near zero'
            })
        except Exception as e:
            results.append({
                'file': filename,
                'error': str(e)
            })

    return jsonify(results)


@app.route('/test_single_pair')
def test_single_pair():
    """Test a single pair with detailed frame-by-frame output"""
    from bvh_parser import calculate_mpjpe
    import os
    from flask import jsonify, request

    left = request.args.get('left', 'walk-low-time.bvh')
    right = request.args.get('right', 'walk-high-time.bvh')

    left_path = os.path.join('static', 'bvh', left)
    right_path = os.path.join('static', 'bvh', right)

    try:
        result = calculate_mpjpe(left_path, right_path)

        # Return first 10 frame errors for debugging
        frame_sample = result['frame_errors'][:10] if len(result['frame_errors']) > 10 else result['frame_errors']

        return jsonify({
            'pair': f"{left} vs {right}",
            'mpjpe': round(result['mpjpe'], 6),
            'num_frames': result['num_frames'],
            'num_joints': result['num_joints'],
            'duration': round(result['duration'], 2),
            'min_error': round(result['min_error'], 6),
            'max_error': round(result['max_error'], 6),
            'first_10_frame_errors': [round(e, 6) for e in frame_sample],
            'python_calculation': 'This is the Python backend ground truth'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/test_all_pairs_python')
def test_all_pairs_python():
    """Calculate MPJPE for ALL pairs using Python - for comparison with JS"""
    from bvh_parser import calculate_mpjpe
    import os
    from flask import jsonify

    results = []

    for cat_idx, category in enumerate(TRIAL_CATEGORIES, 1):
        for pair_idx, pair in enumerate(category, 1):
            left_path = os.path.join('static', 'bvh', pair[0])
            right_path = os.path.join('static', 'bvh', pair[1])

            try:
                result = calculate_mpjpe(left_path, right_path)
                results.append({
                    'category': cat_idx,
                    'pair': pair_idx,
                    'left': pair[0],
                    'right': pair[1],
                    'mpjpe': round(result['mpjpe'], 6),
                    'frames': result['num_frames'],
                    'joints': result['num_joints']
                })
            except Exception as e:
                results.append({
                    'category': cat_idx,
                    'pair': pair_idx,
                    'left': pair[0],
                    'right': pair[1],
                    'error': str(e)
                })

    return jsonify(results)


@app.route('/mpjpe_test')
def mpjpe_test():
    """Test page to compare Python vs JavaScript MPJPE calculations"""
    return render_template('mpjpe_test.html')


if __name__ == '__main__':
    app.run(debug=True)