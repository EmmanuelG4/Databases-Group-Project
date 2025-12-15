from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.handler import execute_query, insert_data

# Blueprint for all data entry related routes
data_entry_bp = Blueprint(
    'data_entry',
    __name__,
    url_prefix='/entry',
    template_folder='../templates'
)


@data_entry_bp.route('/')
def entry_menu():
    # Displays the main data entry menu page
    return render_template('data_entry/entry_menu.html')


@data_entry_bp.route('/degree', methods=['GET', 'POST'])
def add_degree():
    # Handles adding a new degree to the database
    if request.method == 'POST':
        try:
            # Read form inputs
            name = request.form['degree_name']
            level = request.form['degree_level']
            
            # Validate required fields
            if not name or not level:
                flash('Please enter both Degree Name and Degree Level.', 'error')
                return render_template('data_entry/add_degree.html')
            
            # Insert degree into the database
            data = {'degree_name': name, 'degree_level': level}
            insert_data('degree', data)

            flash(f'Degree added: {name} ({level})', 'success')
            return redirect(url_for('data_entry.add_degree'))
        
        except Exception as e:
            # Catch database constraint errors (e.g., duplicates)
            flash(
                'Database Error: Could not add degree. '
                'This name/level combo might already be in the system. '
                f'Details: {e}',
                'error'
            )
            return render_template('data_entry/add_degree.html')
            
    # Render empty form on GET
    return render_template('data_entry/add_degree.html')


@data_entry_bp.route('/course', methods=['GET', 'POST'])
def add_course():
    # Handles inserting a new course record
    if request.method == 'POST':
        try:
            course_num = request.form['course_num']
            course_name = request.form['course_name']
            
            # Ensure both fields are provided
            if not course_num or not course_name:
                flash('Please enter both Course Number and Course Name.', 'error')
                return render_template('data_entry/add_course.html')
            
            # Insert course into database
            data = {'course_num': course_num, 'course_name': course_name}
            insert_data('course', data)

            flash(f'Course added: {course_num} - {course_name}', 'success')
            return redirect(url_for('data_entry.add_course'))
        
        except Exception as e:
            # Handles duplicate course numbers or database issues
            flash(
                'Database Error: Could not add course. '
                'This course number might already exist. '
                f'Details: {e}',
                'error'
            )
            return render_template('data_entry/add_course.html')

    return render_template('data_entry/add_course.html')


@data_entry_bp.route('/instructor', methods=['GET', 'POST'])
def add_instructor():
    # Adds a new instructor to the system
    if request.method == 'POST':
        try:
            instr_id = request.form['instructor_id']
            instr_name = request.form['instructor_name']
            
            # Validate instructor input
            if not instr_id or not instr_name:
                flash('Please enter both Instructor ID and Instructor Name.', 'error')
                return render_template('data_entry/add_instructor.html')
            
            # Insert instructor record
            data = {'instructor_id': instr_id, 'instructor_name': instr_name}
            insert_data('instructor', data)

            flash(f'Instructor added: {instr_name} (ID: {instr_id})', 'success')
            return redirect(url_for('data_entry.add_instructor'))
        
        except Exception as e:
            # Likely caused by duplicate instructor IDs
            flash(
                'Database Error: Could not add instructor. '
                'This ID might already be in the system. '
                f'Details: {e}',
                'error'
            )
            return render_template('data_entry/add_instructor.html')

    return render_template('data_entry/add_instructor.html')


@data_entry_bp.route('/objective', methods=['GET', 'POST'])
def add_objective():
    # Inserts a new learning objective
    if request.method == 'POST':
        try:
            obj_code = request.form['obj_code']
            title = request.form['title']
            description = request.form.get('description')
            
            # Objective code and title are required
            if not obj_code or not title:
                flash('Please enter both Objective Code and Title.', 'error')
                return render_template('data_entry/add_objective.html')
            
            # Insert objective into database
            data = {'obj_code': obj_code, 'title': title, 'description': description}
            insert_data('learning_objective', data)

            flash(f'Objective added: {obj_code} - {title}', 'success')
            return redirect(url_for('data_entry.add_objective'))
        
        except Exception as e:
            # Handles duplicate objectives or constraint violations
            flash(
                'Database Error: Could not add objective. '
                'This code or title might already exist. '
                f'Details: {e}',
                'error'
            )
            return render_template('data_entry/add_objective.html')

    return render_template('data_entry/add_objective.html')


@data_entry_bp.route('/associate_degree_course', methods=['GET', 'POST'])
def associate_course_to_degree():
    # Links a course to a degree and optionally marks it as core
    degrees = execute_query(
        "SELECT degree_name, degree_level FROM degree ORDER BY degree_name"
    )
    courses = execute_query(
        "SELECT course_num, course_name FROM course ORDER BY course_num"
    )

    if request.method == 'POST':
        try:
            # Read degree and course selection from hidden inputs
            degree_name = request.form['degree_name']
            degree_level = request.form['degree_level']
            course_num = request.form['course_num']

            # Checkbox determines whether the course is core
            is_core = 'is_core' in request.form 
            
            data = {
                'degree_name': degree_name,
                'degree_level': degree_level,
                'course_num': course_num,
                'core': is_core
            }
            insert_data('requires', data)

            flash(
                f'Course {course_num} linked to {degree_name} {degree_level}. '
                f'Core: {is_core}.',
                'success'
            )
            return redirect(url_for('data_entry.associate_course_to_degree'))
        
        except Exception as e:
            # Handles invalid links or duplicate relationships
            flash(
                'Database Error: Could not link course to degree. '
                'Make sure the degree and course already exist. '
                f'Details: {e}',
                'error'
            )
            return render_template(
                'data_entry/associate_course_to_degree.html',
                degrees=degrees,
                courses=courses
            )

    return render_template(
        'data_entry/associate_course_to_degree.html',
        degrees=degrees,
        courses=courses
    )


@data_entry_bp.route('/section', methods=['GET', 'POST'])
def add_section():
    # Adds a course section and assigns an instructor
    courses = execute_query(
        "SELECT course_num, course_name FROM course ORDER BY course_num"
    )
    instructors = execute_query(
        "SELECT instructor_id, instructor_name FROM instructor ORDER BY instructor_name"
    )
    terms = ['Spring', 'Summer', 'Fall']

    if request.method == 'POST':
        try:
            # Read section details from the form
            sec_num = request.form['sec_num']
            num_students = request.form['num_students']
            course_num = request.form['course_num']
            sec_term = request.form['sec_term']
            sec_year = request.form['sec_year']
            instructor_id = request.form['instructor_id']

            # Insert section record
            section_data = {
                'sec_num': sec_num,
                'num_students': int(num_students),
                'course_num': course_num,
                'sec_term': sec_term,
                'sec_year': int(sec_year)
            }
            insert_data('section', section_data)
            
            # Insert teaching assignment
            teaches_data = {
                'sec_num': sec_num,
                'course_num': course_num,
                'instructor_id': instructor_id,
                'sec_term': sec_term,
                'sec_year': int(sec_year)
            }
            insert_data('teaches', teaches_data)

            flash(
                f'Section added: {course_num}-{sec_num} ({sec_term} {sec_year}), '
                f'taught by {instructor_id}.',
                'success'
            )
            return redirect(url_for('data_entry.add_section'))
        
        except ValueError:
            # Handles invalid numeric input
            flash(
                'Error: Number of students and Year must be valid whole numbers.',
                'error'
            )
            return render_template(
                'data_entry/add_section.html',
                courses=courses,
                instructors=instructors,
                terms=terms
            )
        except Exception as e:
            # Handles database insert failures
            flash(
                'Database Error: Could not add section or instructor assignment. '
                'Make sure the course and instructor IDs already exist. '
                f'Details: {e}',
                'error'
            )
            return render_template(
                'data_entry/add_section.html',
                courses=courses,
                instructors=instructors,
                terms=terms
            )
    
    return render_template(
        'data_entry/add_section.html',
        courses=courses,
        instructors=instructors,
        terms=terms
    )


@data_entry_bp.route('/associate_obj_course', methods=['GET', 'POST'])
def link_course_objective():
    # Links a learning objective to a course within a specific degree
    degrees = execute_query(
        "SELECT degree_name, degree_level FROM degree ORDER BY degree_name"
    )

    # Only courses already associated with a degree are selectable
    courses = execute_query("""
        SELECT R.course_num, C.course_name 
        FROM requires R
        JOIN course C ON R.course_num = C.course_num
        GROUP BY R.course_num, C.course_name 
        ORDER BY R.course_num
    """)

    objectives = execute_query(
        "SELECT obj_code, title FROM learning_objective ORDER BY obj_code"
    )

    if request.method == 'POST':
        try:
            degree_name = request.form['degree_name']
            degree_level = request.form['degree_level']
            course_num = request.form['course_num']
            obj_code = request.form['obj_code']

            # Validate all required selections
            if not degree_name or not degree_level or not course_num or not obj_code:
                flash(
                    'Please pick a degree, a course, and a learning objective.',
                    'error'
                )
                return render_template(
                    'data_entry/link_course_objective.html',
                    degrees=degrees,
                    courses=courses,
                    objectives=objectives
                )

            # Ensure the course is actually linked to the degree
            req_row = execute_query(
                """
                SELECT core 
                FROM requires
                WHERE degree_name = %s
                  AND degree_level = %s
                  AND course_num = %s
                LIMIT 1;
                """,
                (degree_name, degree_level, course_num),
                fetch_one=True
            )

            if not req_row:
                flash(
                    'This course is not linked to that degree yet. '
                    'First use "Assign Course to Degree".',
                    'error'
                )
                return render_template(
                    'data_entry/link_course_objective.html',
                    degrees=degrees,
                    courses=courses,
                    objectives=objectives
                )

            # Insert objective-course association
            data = {
                'degree_name': degree_name,
                'degree_level': degree_level,
                'course_num': course_num,
                'obj_code': obj_code
            }
            insert_data('associated', data)

            flash(
                f'Objective {obj_code} linked to course {course_num} '
                f'for {degree_name} {degree_level}.',
                'success'
            )
            return redirect(url_for('data_entry.link_course_objective'))
        
        except Exception as e:
            # Handles duplicate links or database errors
            flash(
                'Database Error: Could not link objective. '
                'This link might already exist, or there was a problem with the data. '
                f'Details: {e}',
                'error'
            )
            return render_template(
                'data_entry/link_course_objective.html',
                degrees=degrees,
                courses=courses,
                objectives=objectives
            )

    return render_template(
        'data_entry/link_course_objective.html',
        degrees=degrees,
        courses=courses,
        objectives=objectives
       ) 