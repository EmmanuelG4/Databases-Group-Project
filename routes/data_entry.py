from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db_handler import execute_query, insert_data

# Create the blueprint object
data_entry_bp = Blueprint('data_entry', __name__, url_prefix='/entry', template_folder='../templates')

# --- 0. DATA ENTRY MENU ---
@data_entry_bp.route('/')
def entry_menu():
    """Displays the main menu for all data entry options."""
    return render_template('data_entry/entry_menu.html')

# --------------------------------------------------------------------------
# I. BASIC ENTITY ENTRY (4 Routes)
# --------------------------------------------------------------------------

# --- 1. ADD DEGREE [cite: 41] ---
@data_entry_bp.route('/degree', methods=['GET', 'POST'])
def add_degree():
    if request.method == 'POST':
        try:
            name = request.form['degree_name']
            level = request.form['degree_level']
            
            if not name or not level:
                flash('Degree Name and Level are required.', 'error')
                return render_template('data_entry/add_degree.html')
            
            data = {'degree_name': name, 'degree_level': level}
            insert_data('degree', data)
            flash(f'Successfully added Degree: {name} ({level})', 'success')
            return redirect(url_for('data_entry.add_degree'))
        
        except Exception as e:
            flash(f'Database Error: Could not add degree (Name/Level combination may already exist). Details: {e}', 'error')
            return render_template('data_entry/add_degree.html')
            
    return render_template('data_entry/add_degree.html')


# --- 2. ADD COURSE [cite: 42] ---
@data_entry_bp.route('/course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        try:
            course_num = request.form['course_num']
            course_name = request.form['course_name']
            
            if not course_num or not course_name:
                flash('Course Number and Name are required.', 'error')
                return render_template('data_entry/add_course.html')
            
            data = {'course_num': course_num, 'course_name': course_name}
            insert_data('course', data)
            flash(f'Successfully added Course: {course_num} - {course_name}', 'success')
            return redirect(url_for('data_entry.add_course'))
        
        except Exception as e:
            flash(f'Database Error: Could not add course (Number may already exist). Details: {e}', 'error')
            return render_template('data_entry/add_course.html')

    return render_template('data_entry/add_course.html')


# --- 3. ADD INSTRUCTOR [cite: 43] ---
@data_entry_bp.route('/instructor', methods=['GET', 'POST'])
def add_instructor():
    if request.method == 'POST':
        try:
            instr_id = request.form['instructor_id']
            instr_name = request.form['instructor_name']
            
            if not instr_id or not instr_name:
                flash('Instructor ID and Name are required.', 'error')
                return render_template('data_entry/add_instructor.html')
            
            data = {'instructor_id': instr_id, 'instructor_name': instr_name}
            insert_data('instructor', data)
            flash(f'Successfully added Instructor: {instr_name} (ID: {instr_id})', 'success')
            return redirect(url_for('data_entry.add_instructor'))
        
        except Exception as e:
            flash(f'Database Error: Could not add instructor (ID may already exist). Details: {e}', 'error')
            return render_template('data_entry/add_instructor.html')

    return render_template('data_entry/add_instructor.html')


# --- 4. ADD LEARNING OBJECTIVE [cite: 46] ---
@data_entry_bp.route('/objective', methods=['GET', 'POST'])
def add_objective():
    if request.method == 'POST':
        try:
            obj_code = request.form['obj_code']
            title = request.form['title']
            description = request.form.get('description')
            
            if not obj_code or not title:
                flash('Objective Code and Title are required.', 'error')
                return render_template('data_entry/add_objective.html')
            
            data = {'obj_code': obj_code, 'title': title, 'description': description}
            insert_data('learning_objective', data)
            flash(f'Successfully added Objective: {obj_code} - {title}', 'success')
            return redirect(url_for('data_entry.add_objective'))
        
        except Exception as e:
            flash(f'Database Error: Could not add objective (Code or Title may already exist). Details: {e}', 'error')
            return render_template('data_entry/add_objective.html')

    return render_template('data_entry/add_objective.html')


# --------------------------------------------------------------------------
# II. ASSOCIATIVE ENTRY (3 Routes)
# --------------------------------------------------------------------------

# --- 5. ASSOCIATE COURSE TO DEGREE (REQUIRES) ---
@data_entry_bp.route('/associate_degree_course', methods=['GET', 'POST'])
def associate_course_to_degree():
    """Handles linking a Course to a Degree and setting the CORE status."""
    if request.method == 'POST':
        try:
            degree_name = request.form['degree_name']
            degree_level = request.form['degree_level']
            course_num = request.form['course_num']
            # Checkbox returns 'on' if checked, otherwise absent from request.form
            is_core = 'is_core' in request.form 
            
            data = {
                'degree_name': degree_name, 
                'degree_level': degree_level, 
                'course_num': course_num, 
                'core': is_core
            }
            insert_data('requires', data)
            flash(f'Course {course_num} assigned to {degree_name} {degree_level}. Core status: {is_core}.', 'success')
            return redirect(url_for('data_entry.associate_course_to_degree'))
        
        except Exception as e:
            flash(f'Database Error: Could not associate course. Ensure Degree and Course exist. Details: {e}', 'error')
            return render_template('data_entry/associate_course_to_degree.html')

    # Fetch data for dropdowns (using dictionary access)
    degrees = execute_query("SELECT degree_name, degree_level FROM degree ORDER BY degree_name")
    courses = execute_query("SELECT course_num, course_name FROM course ORDER BY course_num")

    return render_template('data_entry/associate_course_to_degree.html', degrees=degrees, courses=courses)


# --- 6. ENTER COURSE/SECTION FOR A GIVEN SEMESTER (Section and Teaches) [cite: 44, 49] ---
@data_entry_bp.route('/section', methods=['GET', 'POST'])
def add_section():
    """Inserts records into the SECTION and TEACHES tables."""
    if request.method == 'POST':
        try:
            sec_num = request.form['sec_num']
            num_students = request.form['num_students']
            course_num = request.form['course_num']
            sec_term = request.form['sec_term']
            sec_year = request.form['sec_year']
            instructor_id = request.form['instructor_id']

            # 1. Insert into the SECTION table
            section_data = {
                'sec_num': sec_num, 
                'num_students': int(num_students), 
                'course_num': course_num, 
                'sec_term': sec_term, 
                'sec_year': int(sec_year)
            }
            insert_data('section', section_data)
            
            # 2. Insert into the TEACHES table (linking section to instructor)
            teaches_data = {
                'sec_num': sec_num, 
                'course_num': course_num, 
                'sec_term': sec_term, 
                'sec_year': int(sec_year), 
                'instructor_id': instructor_id
            }
            insert_data('teaches', teaches_data)

            flash(f'Successfully offered section {course_num}-{sec_num} ({sec_term} {sec_year}) by Instructor {instructor_id}.', 'success')
            return redirect(url_for('data_entry.add_section'))
        
        except ValueError:
            flash('Error: Number of students and Year must be valid integers.', 'error')
            return redirect(url_for('data_entry.add_section'))
        except Exception as e:
            flash(f'Database Error: Could not add section or assignment. Ensure Course and Instructor IDs exist. Details: {e}', 'error')
            return render_template('data_entry/add_section.html')

    # Query existing data for dropdowns
    courses = execute_query("SELECT course_num, course_name FROM course ORDER BY course_num")
    instructors = execute_query("SELECT instructor_id, instructor_name FROM instructor ORDER BY instructor_name")
    terms = ['Spring', 'Summer', 'Fall'] # Fixed list of terms [cite: 14]
    
    return render_template('data_entry/add_section.html', courses=courses, instructors=instructors, terms=terms)


# --- 7. ASSOCIATING COURSES WITH OBJECTIVES (ASSOCIATED) [cite: 47] ---
@data_entry_bp.route('/associate_obj_course', methods=['GET', 'POST'])
def link_course_objective():
    """Handles linking a CORE course for a Degree to a Learning Objective."""
    if request.method == 'POST':
        try:
            degree_name = request.form['degree_name']
            degree_level = request.form['degree_level']
            course_num = request.form['course_num']
            obj_code = request.form['obj_code']

            # A check should ideally be run here to ensure the course_num is marked 
            # as CORE for the specified degree in the 'requires' table.
            
            data = {
                'degree_name': degree_name, 
                'degree_level': degree_level, 
                'course_num': course_num, 
                'obj_code': obj_code
            }
            insert_data('associated', data)
            flash(f'Objective {obj_code} linked to core course {course_num} for {degree_name} {degree_level}.', 'success')
            return redirect(url_for('data_entry.link_course_objective'))
        
        except Exception as e:
            flash(f'Database Error: Could not link objective (Link may already exist). Details: {e}', 'error')
            return render_template('data_entry/link_course_objective.html')

    # Query existing data for dropdowns
    degrees = execute_query("SELECT degree_name, degree_level FROM degree ORDER BY degree_name")
    # Optimize course selection: only show courses marked as CORE in the requires table
    courses = execute_query("""
        SELECT R.course_num, C.course_name 
        FROM requires R
        JOIN course C ON R.course_num = C.course_num
        WHERE R.core = TRUE
        GROUP BY R.course_num, C.course_name 
        ORDER BY R.course_num
    """)
    objectives = execute_query("SELECT obj_code, title FROM learning_objective ORDER BY obj_code")

    return render_template('data_entry/link_course_objective.html', degrees=degrees, courses=courses, objectives=objectives)