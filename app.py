from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import random

app = Flask(__name__)

# Constants
classrooms = [f'C{i}' for i in range(1, 21)]  # 20 classrooms
teachers = [f'T{i}' for i in range(1, 5)]  # 4 teachers
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
class_durations = [1, 2]  # 1-hour or 2-hour class
batches = [f'B{i}' for i in range(1, 6)]  # 5 batches

# Time slots for each day
time_slots = {day: [(hour, hour + 1) for hour in range(8, 18)] for day in days}

timetable = []  # Store schedules
classes_per_batch = 25  # Total classes per batch
num_classes_per_day = {day: random.randint(3, 5) for day in days}  # Classes per day

# Helper function to get a random time slot
def get_random_time_slot(day):
    return random.choice(time_slots[day])

# Generate timetable
for batch in batches:
    total_classes_scheduled = 0
    for day in days:
        num_classes = num_classes_per_day[day]
        if total_classes_scheduled + num_classes > classes_per_batch:
            num_classes = classes_per_batch - total_classes_scheduled
        
        for _ in range(num_classes):
            teacher = random.choice(teachers)
            classroom = random.choice(classrooms)
            if len(time_slots[day]) == 0:
                continue
            start_time, end_time = get_random_time_slot(day)
            duration = random.choice(class_durations)
            actual_end_time = min(start_time + duration, 18)
            timetable.append([batch, teacher, classroom, day, start_time, actual_end_time])
            total_classes_scheduled += 1
            for hour in range(start_time, actual_end_time):
                time_slot_to_remove = (hour, hour + 1)
                if time_slot_to_remove in time_slots[day]:
                    time_slots[day].remove(time_slot_to_remove)
        if not time_slots[day]:
            time_slots[day] = [(hour, hour + 1) for hour in range(8, 18)]
        if total_classes_scheduled >= classes_per_batch:
            break

# Create and sort DataFrame
df = pd.DataFrame(timetable, columns=['Batch', 'Teacher', 'Classroom', 'Day', 'Start Time', 'End Time'])
df['Day'] = pd.Categorical(df['Day'], categories=days, ordered=True)
df = df.sort_values(by=['Batch', 'Day', 'Start Time'])

# Insert blank rows
def insert_blank_rows(df):
    new_df = pd.DataFrame()
    for batch in df['Batch'].unique():
        batch_df = df[df['Batch'] == batch]
        new_df = pd.concat([new_df, batch_df], axis=0)
        blank_row = pd.DataFrame([['', '', '', '', '', '']], columns=df.columns)
        new_df = pd.concat([new_df, blank_row], axis=0)
    return new_df

final_df = insert_blank_rows(df)
timetable_html = final_df.to_html(classes='table table-striped', index=False)

def list_empty_slots(day, time, df, classrooms):
    occupied_classrooms = df[(df['Day'] == day) & (df['Start Time'] <= time) & (df['End Time'] > time)]['Classroom'].tolist()
    return [classroom for classroom in classrooms if classroom not in occupied_classrooms]

def list_ongoing_classes(day, time, df):
    return df[(df['Day'] == day) & (df['Start Time'] <= time) & (df['End Time'] > time)]

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

@app.route('/check_slots', methods=['GET'])
def check_slots():
    day = request.args.get('day')
    time = int(request.args.get('time'))
    empty_classrooms = list_empty_slots(day, time, df, classrooms)
    ongoing_classes = list_ongoing_classes(day, time, df)
    ongoing_classes_html = ongoing_classes.to_html(classes='table table-striped', index=False)
    return render_template('check_slots.html', day=day, time=time, empty_classrooms=empty_classrooms, ongoing_classes_html=ongoing_classes_html)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
