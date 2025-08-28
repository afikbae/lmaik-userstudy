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
]

# Define the pairs of motions, now grouped into categories (parts).
# Each trial will randomly select one pair from its corresponding category.
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
# For a real study, you would populate these with the actual BVH file pairs for each category.

TOTAL_TRIALS = len(TRIAL_CATEGORIES)
RESULTS_FILE = os.path.join('results', 'study_results.csv')

# Ensure the results directory exists
os.makedirs('results', exist_ok=True)

# --- Routes ---

@app.route('/')
def index():
    # Redirect to the main study page
    return redirect(url_for('user_study'))

@app.route('/userstudy', methods=['GET', 'POST'])
def user_study():
    if request.method == 'POST':
        prolific_id = request.form.get('prolific_id')
        if not prolific_id:
            return render_template('login.html', error="Prolific ID cannot be empty.")
        
        session['prolific_id'] = prolific_id
        session['current_trial'] = 1 # Start with the first trial
        
        # You could also shuffle your trial pairs here if needed
        # random.shuffle(TRIAL_PAIRS) 
        # session['trial_pairs'] = TRIAL_PAIRS
        
        return redirect(url_for('run_trial', trial_num=1))
        
    # On GET, just show the login page
    return render_template('login.html')

@app.route('/trial/<int:trial_num>', methods=['GET', 'POST'])
def run_trial(trial_num):
    # Security checks: ensure user has a session and is on the correct trial
    if 'prolific_id' not in session:
        return redirect(url_for('user_study'))
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
        for i in range(1, 18):
            form_value = request.form.get(f'q{i}', 'N/A')
            answers_numerical[f'q{i}'] = choice_mapping.get(form_value, -1)
        
        # Construct the 'R' string as per Realism Personality.html format
        choices_string = ",".join(str(answers_numerical[f'q{i}']) for i in range(1, 18))
        
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
            'SNO': trial_num, # SNO seems to be the trial number/category
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

    # Get the category of pairs for the current trial
    category_pairs = TRIAL_CATEGORIES[trial_num - 1]
    
    # Randomly select a pair from the category and store its index
    mod_no = random.randrange(len(category_pairs))
    session['current_mod_no'] = mod_no
    motion_pair_for_trial = category_pairs[mod_no]

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


if __name__ == '__main__':
    app.run(debug=True)