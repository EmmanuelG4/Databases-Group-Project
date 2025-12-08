from flask import Blueprint, render_template, request, flash, redirect, url_for
from database.handler import execute_query

# Create the blueprint object
querying_bp = Blueprint('querying', __name__, url_prefix='/query', template_folder='../templates')

# --- 0. QUERY MENU ---
@querying_bp.route('/')
def query_menu():
    """Displays the main menu for all query options."""
    return render_template('querying/query_menu.html')

# --------------------------------------------------------------------------
# I. DEGREE-BASED QUERIES [cite: 58-63]
# --------------------------------------------------------------------------

@querying_bp.route('/degree_details', methods=['GET', 'POST'])
def query_degree_details():
    """Lists courses (core/non-core) and objectives for a given degree."""
    
    degrees = execute_query("SELECT degree_name, degree_level FROM degree ORDER BY degree_name")
    results = None
    
    if request.method == 'POST':
        try:
            degree_combined = request.form['degree_select']
            degree_name, degree_level = degree_combined.split('|')

            # Query 1: List all courses associated with the degree (denote which are core) [cite: 59]
            courses_query = """
                SELECT R.course_num, C.course_name, R.core 
                FROM requires R
                JOIN course C ON R.course_num = C.course_num
                WHERE R.degree_name = %s AND R.degree_level = %s
                ORDER BY R.core DESC, R.course_num
            """
            courses = execute_query(courses_query, (degree_name, degree_level))

            # Query 2: List all objectives for the degree [cite: 61]
            objectives_query = """
                SELECT L.obj_code, L.title, L.description
                FROM learning_objective L
                JOIN associated A ON L.obj_code = A.obj_code
                WHERE A.degree_name = %s AND A.degree_level = %s
                GROUP BY L.obj_code, L.title, L.description
                ORDER BY L.obj_code
            """
            objectives = execute_query(objectives_query, (degree_name, degree_level))

            # Query 3: List courses associated with each objective [cite: 62]
            # This is complex and best handled in the template for simplicity, 
            # but we'll fetch all associated links here.
            associated_query = """
                SELECT A.obj_code, A.course_num
                FROM associated A
                WHERE A.degree_name = %s AND A.degree_level = %s
            """
            associated_links = execute_query(associated_query, (degree_name, degree_level))

            results = {
                'degree_name': degree_name,
                'degree_level': degree_level,
                'courses': courses,
                'objectives': objectives,
                'associated_links': associated_links
            }
            
        except Exception as e:
            flash(f'Error running degree query. Details: {e}', 'error')

    return render_template('querying/degree_details.html', degrees=degrees, results=results)


@querying_bp.route('/degree_sections', methods=['GET', 'POST'])
def query_degree_sections():
    """Lists all sections offered for courses within a degree in a time range (chronological order)[cite: 60]."""
    
    degrees = execute_query("SELECT degree_name, degree_level FROM degree ORDER BY degree_name")
    sections = None

    if request.method == 'POST':
        try:
            degree_combined = request.form['degree_select']
            degree_name, degree_level = degree_combined.split('|')
            start_year = request.form['start_year']
            end_year = request.form['end_year']
            
            # Query all sections that belong to courses required by the selected degree
            sections_query = """
                SELECT S.course_num, C.course_name, S.sec_num, S.sec_term, S.sec_year, R.core
                FROM section S
                JOIN course C ON S.course_num = C.course_num
                JOIN requires R ON S.course_num = R.course_num 
                                AND R.degree_name = %s AND R.degree_level = %s
                WHERE S.sec_year BETWEEN %s AND %s
                ORDER BY S.sec_year, FIELD(S.sec_term, 'Spring', 'Summer', 'Fall'), S.course_num
            """
            sections = execute_query(sections_query, (degree_name, degree_level, start_year, end_year))

        except Exception as e:
            flash(f'Error querying degree sections. Details: {e}', 'error')

    return render_template('querying/degree_sections.html', degrees=degrees, sections=sections)


# --------------------------------------------------------------------------
# II. COURSE/INSTRUCTOR-BASED QUERIES [cite: 64-68]
# --------------------------------------------------------------------------

@querying_bp.route('/course_sections', methods=['GET', 'POST'])
def query_course_sections():
    """Lists all sections of a course for a specific range of semesters[cite: 65]."""
    
    courses = execute_query("SELECT course_num, course_name FROM course ORDER BY course_num")
    sections = None

    if request.method == 'POST':
        try:
            course_num = request.form['course_select']
            start_year = request.form['start_year']
            end_year = request.form['end_year']

            sections_query = """
                SELECT S.sec_num, S.sec_term, S.sec_year, S.num_students, I.instructor_name
                FROM section S
                LEFT JOIN teaches T ON S.sec_num = T.sec_num AND S.course_num = T.course_num 
                                     AND S.sec_term = T.sec_term AND S.sec_year = T.sec_year
                LEFT JOIN instructor I ON T.instructor_id = I.instructor_id
                WHERE S.course_num = %s AND S.sec_year BETWEEN %s AND %s
                ORDER BY S.sec_year, FIELD(S.sec_term, 'Spring', 'Summer', 'Fall')
            """
            sections = execute_query(sections_query, (course_num, start_year, end_year))

        except Exception as e:
            flash(f'Error querying course sections. Details: {e}', 'error')

    return render_template('querying/course_sections.html', courses=courses, sections=sections)


@querying_bp.route('/instructor_sections', methods=['GET', 'POST'])
def query_instructor_sections():
    """Lists all the sections that an instructor has taught (given a range of semesters)[cite: 68]."""
    
    instructors = execute_query("SELECT instructor_id, instructor_name FROM instructor ORDER BY instructor_name")
    sections = None

    if request.method == 'POST':
        try:
            instructor_id = request.form['instructor_select']
            start_year = request.form['start_year']
            end_year = request.form['end_year']

            sections_query = """
                SELECT T.course_num, C.course_name, T.sec_num, T.sec_term, T.sec_year
                FROM teaches T
                JOIN section S ON T.sec_num = S.sec_num AND T.course_num = S.course_num 
                                 AND T.sec_term = S.sec_term AND T.sec_year = S.sec_year
                JOIN course C ON T.course_num = C.course_num
                WHERE T.instructor_id = %s AND T.sec_year BETWEEN %s AND %s
                ORDER BY T.sec_year, FIELD(T.sec_term, 'Spring', 'Summer', 'Fall')
            """
            sections = execute_query(sections_query, (instructor_id, start_year, end_year))

        except Exception as e:
            flash(f'Error querying instructor sections. Details: {e}', 'error')

    return render_template('querying/instructor_sections.html', instructors=instructors, sections=sections)


# --------------------------------------------------------------------------
# III. EVALUATION-BASED QUERIES [cite: 69-72]
# --------------------------------------------------------------------------

@querying_bp.route('/evaluation_status', methods=['GET', 'POST'])
def query_evaluation_status():
    """Determines evaluation entry status for all sections in a given semester[cite: 70]."""
    
    results = None
    if request.method == 'POST':
        try:
            sec_term = request.form['sec_term']
            sec_year = request.form['sec_year']
            
            # Required Query: List all sections for the semester and determine status (Full/Partial/None)
            
            # Step 1: Get all sections offered this semester
            sections_query = """
                SELECT 
                    S.course_num, S.sec_num, S.sec_term, S.sec_year, 
                    C.course_name, S.num_students, I.instructor_name
                FROM section S
                JOIN course C ON S.course_num = C.course_num
                LEFT JOIN teaches T ON S.sec_num = T.sec_num AND S.course_num = T.course_num 
                                    AND S.sec_term = T.sec_term AND S.sec_year = T.sec_year
                LEFT JOIN instructor I ON T.instructor_id = I.instructor_id
                WHERE S.sec_term = %s AND S.sec_year = %s
                ORDER BY S.course_num, S.sec_num
            """
            sections = execute_query(sections_query, (sec_term, sec_year))
            
            results = []
            
            for section in sections:
                course_num = section['course_num']
                
                # Step 2: Get all degrees associated with this course and the number of objectives
                # We need the total expected number of evaluations for this course/section.
                total_expected_evals_query = """
                    SELECT 
                        R.degree_name, R.degree_level, COUNT(A.obj_code) AS total_objs
                    FROM requires R
                    LEFT JOIN associated A ON R.course_num = A.course_num 
                                            AND R.degree_name = A.degree_name
                                            AND R.degree_level = A.degree_level
                    WHERE R.course_num = %s 
                    AND R.core = TRUE -- Only core courses have associated objectives
                    GROUP BY R.degree_name, R.degree_level
                """
                expected_evals = execute_query(total_expected_evals_query, (course_num,))
                
                section_data = section
                section_data['evaluations'] = []
                
                for expected in expected_evals:
                    degree_name = expected['degree_name']
                    degree_level = expected['degree_level']
                    total_objs = expected['total_objs']
                    
                    # Step 3: Count how many evaluations have been entered for this section/degree
                    entered_evals_query = """
                        SELECT 
                            COUNT(*) AS entered_count,
                            SUM(CASE WHEN improvements IS NOT NULL AND improvements != '' THEN 1 ELSE 0 END) AS improve_count
                        FROM objective_eval
                        WHERE sec_term = %s AND sec_year = %s AND course_num = %s 
                        AND degree_name = %s AND degree_level = %s
                    """
                    eval_counts = execute_query(entered_evals_query, (sec_term, sec_year, course_num, degree_name, degree_level), fetch_one=True)
                    
                    entered_count = eval_counts['entered_count']
                    improve_count = eval_counts['improve_count']
                    
                    # Determine Status [cite: 70]
                    status = 'Not Entered'
                    if total_objs > 0:
                        if entered_count == total_objs:
                            status = 'Fully Entered'
                        elif entered_count > 0:
                            status = f'Partially Entered ({entered_count}/{total_objs})'
                    elif entered_count > 0:
                         # Handle case where evaluation exists but objectives weren't set up (shouldn't happen in proper data)
                         status = 'Data Exists (No Objectives Set)'

                    section_data['evaluations'].append({
                        'degree': f"{degree_name} ({degree_level})",
                        'status': status,
                        'improvement_paragraph': 'Entered' if improve_count > 0 else 'Missing' 
                    })
                
                results.append(section_data)

        except Exception as e:
            flash(f'Error running evaluation status query. Details: {e}', 'error')

    return render_template('querying/evaluation_status.html', results=results, terms=['Spring', 'Summer', 'Fall'])


@querying_bp.route('/grade_percentage', methods=['GET', 'POST'])
def query_grade_percentage():
    """Outputs sections where the number of non-'F' students meets a user-supplied percentage[cite: 71]."""
    
    sections = None
    if request.method == 'POST':
        try:
            sec_term = request.form['sec_term']
            sec_year = request.form['sec_year']
            percentage = float(request.form['percentage']) / 100.0
            
            # Find sections where the SUM of (A + B + C) grades for an objective
            # is greater than or equal to the required percentage of total students.
            
            # Note: This query assumes the objective_eval records (A, B, C, F counts)
            # are representative of the whole section's enrollment (num_students).
            
            grade_query = """
                SELECT 
                    OE.course_num, OE.sec_num, C.course_name, OE.sec_term, OE.sec_year,
                    S.num_students, OE.degree_name, OE.degree_level,
                    SUM(OE.perform_a + OE.perform_b + OE.perform_c) AS total_non_f,
                    SUM(OE.perform_a + OE.perform_b + OE.perform_c + OE.perform_f) AS total_grades_entered
                FROM objective_eval OE
                JOIN section S ON OE.course_num = S.course_num AND OE.sec_num = S.sec_num
                                AND OE.sec_term = S.sec_term AND OE.sec_year = S.sec_year
                JOIN course C ON OE.course_num = C.course_num
                WHERE OE.sec_term = %s AND OE.sec_year = %s
                GROUP BY 
                    OE.course_num, OE.sec_num, C.course_name, OE.sec_term, OE.sec_year,
                    S.num_students, OE.degree_name, OE.degree_level
                HAVING SUM(OE.perform_a + OE.perform_b + OE.perform_c) >= S.num_students * %s
                ORDER BY OE.course_num, OE.sec_num, OE.degree_name
            """
            # Note: The HAVING clause is the core of the percentage filter [cite: 71]
            sections = execute_query(grade_query, (sec_term, sec_year, percentage))

        except ValueError:
            flash('Error: Percentage must be a valid number.', 'error')
        except Exception as e:
            flash(f'Error running grade percentage query. Details: {e}', 'error')

    return render_template('querying/grade_percentage.html', sections=sections, terms=['Spring', 'Summer', 'Fall'])