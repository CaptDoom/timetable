from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import random

app = Flask(__name__)

# Constants
classrooms = [f'C{i}' for i in range(1, 21)]  # 20 classrooms
teachers = [f'T{i}' for i in range(1, 5)]  # 4 teachers
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
class_durations = [1, 2]  # 1-hour or 2-hour class

# List of batches
batches = [f'B{i}' for i in range(1, 6)]  # 5 batches: B1, B2, ..., B5

# Dictionary to store available time slots for each day
time_slots = {day: [(hour, hour + 1) for hour in range(8, 18)] for day in days}

# Timetable list to store all schedules
timetable = []

# Fixed number of classes per batch
classes_per_batch = 25  # Set this to the total number of classes each batch should have

# Classes distributed over the week (3 to 5 per day to total 25 classes for each batch)
num_classes_per_day = {day: random.randint(3, 5) for day in days}

# Helper function to get a random time slot for a specific day
def get_random_time_slot(day):
    return random.choice(time_slots[day])

# Generate timetable for all batches
for batch in batches:
    total_classes_scheduled = 0
    
    # Schedule classes for each batch
    for day in days:
        num_classes = num_classes_per_day[day]
        
        # Check if remaining classes are fewer than the current day allows
        if total_classes_scheduled + num_classes > classes_per_batch:
            num_classes = classes_per_batch - total_classes_scheduled  # Only schedule remaining classes
        
        for _ in range(num_classes):
            # Randomly select teacher, classroom, and time slot
            teacher = random.choice(teachers)
            classroom = random.choice(classrooms)
            
            # Get a valid time slot and calculate the end time based on the class duration
            if len(time_slots[day]) == 0:
                continue  # No available time slots for this day
            
            start_time, end_time = get_random_time_slot(day)
            duration = random.choice(class_durations)
            actual_end_time = min(start_time + duration, 18)  # Make sure class doesn't go beyond 6 PM
            
            # Append class details to timetable
            timetable.append([batch, teacher, classroom, day, start_time, actual_end_time])
            total_classes_scheduled += 1
            
            # Remove used time slots (for each hour in the duration)
            for hour in range(start_time, actual_end_time):
                time_slot_to_remove = (hour, hour + 1)
                if time_slot_to_remove in time_slots[day]:
                    time_slots[day].remove(time_slot_to_remove)  # Remove only if the time slot exists
        
        # Reset time slots for the next day if all are used
        if not time_slots[day]:
            time_slots[day] = [(hour, hour + 1) for hour in range(8, 18)]
        
        # Stop if we've scheduled all classes for this batch
        if total_classes_scheduled >= classes_per_batch:
            break

# Create a DataFrame to display the timetable
df = pd.DataFrame(timetable, columns=['Batch', 'Teacher', 'Classroom', 'Day', 'Start Time', 'End Time'])

# Sort the timetable by 'Batch', 'Day', and 'Start Time'
df['Day'] = pd.Categorical(df['Day'], categories=days, ordered=True)  # Ensure correct day order
df = df.sort_values(by=['Batch', 'Day', 'Start Time'])

# Insert blank rows between each batch
def insert_blank_rows(df):
    new_df = pd.DataFrame()
    batches = df['Batch'].unique()
    
    for batch in batches:
        # Append the batch timetable
        batch_df = df[df['Batch'] == batch]
        new_df = pd.concat([new_df, batch_df], axis=0)
        
        # Append a blank row after each batch
        blank_row = pd.DataFrame([['', '', '', '', '', '']], columns=df.columns)
        new_df = pd.concat([new_df, blank_row], axis=0)
    
    return new_df

# Insert blank rows
final_df = insert_blank_rows(df)

# Convert final DataFrame to HTML
timetable_html = final_df.to_html(classes='table table-striped', index=False)

@app.route('/')
def index():
    return render_template('index.html', timetable_html=timetable_html)

@app.route('/batch')
def batch():
    batch_number = request.args.get('batch_number')
    if batch_number:
        batch_timetable = df[df['Batch'] == batch_number]
        if batch_timetable.empty:
            return f"No timetable found for batch {batch_number}", 404
        return render_template('timetable.html', timetable_html=batch_timetable.to_html(classes='table table-striped', index=False))
    return redirect(url_for('index'))

@app.route('/teacher')
def teacher():
    teacher_id = request.args.get('teacher_id')
    if teacher_id:
        teacher_timetable = df[df['Teacher'] == teacher_id]
        if teacher_timetable.empty:
            return f"No classes found for teacher {teacher_id}", 404
        return render_template('timetable.html', timetable_html=teacher_timetable.to_html(classes='table table-striped', index=False))
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True,port=8000)
