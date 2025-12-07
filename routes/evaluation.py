from flask import Blueprint, render_template, request, flash, redirect, url_for
from database.db_handler import execute_query

# Create the Blueprint object
evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation', template_folder='../templates')

# --- 1. SELECTION PAGE ---
@evaluation_bp.route('/', methods=['GET'])
@evaluation_bp.route('/select', methods=['GET'])
def select_evaluation():
    """Step 1: Displays the form to select Degree, Instructor, and Semester."""
    try:
        # Fetch data for dropdowns
        degrees = execute_query("SELECT degree_name, degree_level FROM degree ORDER BY degree_name")
        instructors = execute_query("SELECT instructor_id, instructor_name FROM instructor ORDER BY instructor_name")
        
        # NOTE: Semester terms (Fall, Spring, Summer) and years would ideally be pulled 
        # from a unique list in the 'section' table if possible, or hardcoded for a basic GUI.

        return render_template('evaluation/eval_select.html', 
                               degrees=degrees, 
                               instructors=instructors,
                               terms=['Fall', 'Spring', 'Summer'])
    except Exception as e:
        flash(f'Error loading selection data: {e}', 'error')
        return redirect(url_for('index'))


# --- 2. LIST/STATUS CHECK PAGE ---
@evaluation_bp.route('/list_sections', methods=['GET'])
def list_sections_status():
    """Step 2: Lists sections taught by instructor and checks evaluation status."""
    
    # 1. Grab context data from the selection form (via URL query parameters)
    degree_combined = request.args.get('degree')
    instructor_id = request.args.get('instructor_id')
    sec_term = request.args.get('sec_term')
    sec_year = request.args.get('sec_year')

    if not all([degree_combined, instructor_id, sec_term, sec_year]):
        flash("Please select all criteria (Degree, Instructor, Term, Year).", 'error')
        return redirect(url_for('evaluation.select_evaluation'))

    degree_name, degree_level = degree_combined.split('|')

    # 2. Query all sections taught by this instructor in this semester
    # This query uses the composite key for the 'section' table
    query_sections = """
        SELECT S.sec_num, S.course_num, S.sec_term, S.sec_year, C.course_name, S.num_students
        FROM teaches T
        JOIN section S ON T.sec_num = S.sec_num AND T.course_num = S.course_num 
                         AND T.sec_term = S.sec_term AND T.sec_year = S.sec_year
        JOIN course C ON S.course_num = C.course_num
        WHERE T.instructor_id = %s AND T.sec_term = %s AND T.sec_year = %s
    """
    sections = execute_query(query_sections, (instructor_id, sec_term, sec_year))

    sections_data = []
    
    for section in sections:
        course_num = section['course_num']
        
        # Get all objectives associated with this course and the selected degree
        query_objs = """
            SELECT L.obj_code, L.title
            FROM associated A
            JOIN learning_objective L ON A.obj_code = L.obj_code
            WHERE A.degree_name = %s AND A.degree_level = %s AND A.course_num = %s
        """
        objectives = execute_query(query_objs, (degree_name, degree_level, course_num))
        
        eval_count = 0
        total_obj_count = len(objectives)
        
        for obj in objectives:
            # Check if evaluation exists for this objective/section/degree
            check_eval = """
                SELECT improvements FROM objective_eval
                WHERE sec_num = %s AND sec_term = %s AND sec_year = %s
                AND obj_code = %s AND degree_name = %s AND degree_level = %s
                AND course_num = %s
            """
            eval_data = execute_query(check_eval, (
                section['sec_num'], sec_term, sec_year,
                obj['obj_code'], degree_name, degree_level, course_num
            ), fetch_one=True)
            
            if eval_data:
                eval_count += 1
                # Check for optional improvement paragraph [cite: 70]
                obj['improvement_entered'] = bool(eval_data.get('improvements')) 
            
            obj['status'] = 'Entered' if eval_data else 'Missing'

        # Determine overall section status (Full, Partial, Not Entered) [cite: 70]
        status = 'Not Entered'
        if total_obj_count > 0:
            if eval_count == total_obj_count:
                status = 'Fully Entered'
            elif eval_count > 0:
                status = f'Partially Entered ({eval_count}/{total_obj_count})'

        sections_data.append({
            'section': section,
            'objectives': objectives,
            'status': status
        })

    # Render the entry page/status list 
    return render_template('evaluation/eval_entry.html', 
                            sections_data=sections_data, 
                            context={'degree_name': degree_name, 
                                     'degree_level': degree_level, 
                                     'instructor_id': instructor_id,
                                     'sec_term': sec_term,
                                     'sec_year': sec_year})


# --- 3. SAVE EVALUATION (Includes UPSERT and Duplication) ---
@evaluation_bp.route('/save', methods=['POST'])
def save_evaluation():
    # Helper to check if a row exists in objective_eval
    def check_exists(cursor, params):
        check_query = """
            SELECT 1 FROM objective_eval
            WHERE sec_num=%s AND sec_term=%s AND sec_year=%s 
            AND obj_code=%s AND degree_name=%s AND degree_level=%s AND course_num=%s
        """
        # Note: We must get a connection that allows us to manage transactions manually here
        cursor.execute(check_query, params)
        return cursor.fetchone()

    # Get connection from the application context
    conn = execute_query(None, use_conn=True) # Use a dummy call to get the active connection
    cursor = conn.cursor()
    
    # 1. Grab context (Degree and Semester are hidden fields in the form)
    degree_name_context = request.form.get('degree_name')
    degree_level_context = request.form.get('degree_level')
    sec_term_context = request.form.get('sec_term')
    sec_year_context = request.form.get('sec_year')
    
    saved_count = 0
    
    try:
        # 2. Loop through submitted data (form fields are named like: CS5330|001|LO-A1|based_on)
        for key, value in request.form.items():
            if '|' in key and key.endswith('|based_on'):
                parts = key.split('|')
                course_num, sec_num, obj_code, _ = parts
                
                # Retrieve all related data fields for this objective/section
                prefix = f"{course_num}|{sec_num}|{obj_code}|"
                
                based_on = value
                perform_a = int(request.form.get(prefix + 'perform_a') or 0)
                perform_b = int(request.form.get(prefix + 'perform_b') or 0)
                perform_c = int(request.form.get(prefix + 'perform_c') or 0)
                perform_f = int(request.form.get(prefix + 'perform_f') or 0)
                improvements = request.form.get(prefix + 'improvements')
                
                # Optional: Check student count validation (as done in your original attempt)
                # ... (SQL to check num_students and validate total_entered) ...
                
                # Base parameters for the evaluation record
                eval_params = (
                    based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                    sec_num, sec_term_context, sec_year_context, obj_code, 
                    degree_name_context, degree_level_context, course_num
                )
                
                # Check for existing record (UPSERT logic)
                where_params = eval_params[6:] # The last 7 items are the composite PK
                exists = check_exists(cursor, where_params)
                
                if exists:
                    # UPDATE existing row
                    update_query = """
                        UPDATE objective_eval SET based_on=%s, perform_a=%s, perform_b=%s, 
                        perform_c=%s, perform_f=%s, improvements=%s
                        WHERE sec_num=%s AND sec_term=%s AND sec_year=%s AND obj_code=%s 
                        AND degree_name=%s AND degree_level=%s AND course_num=%s
                    """
                    cursor.execute(update_query, eval_params)
                else:
                    # INSERT new row
                    insert_query = """
                        INSERT INTO objective_eval (based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                        sec_num, sec_term, sec_year, obj_code, degree_name, degree_level, course_num)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, eval_params)
                
                saved_count += 1
                
                # --- DUPLICATION LOGIC  ---
                duplicate_key = f"{prefix}duplicate"
                if request.form.get(duplicate_key) == 'on':
                    
                    query_other_degrees = """
                        SELECT DISTINCT A.degree_name, A.degree_level 
                        FROM associated A
                        WHERE A.course_num = %s AND A.obj_code = %s
                        AND NOT (A.degree_name = %s AND A.degree_level = %s)
                    """
                    cursor.execute(query_other_degrees, (course_num, obj_code, degree_name_context, degree_level_context))
                    other_degrees = cursor.fetchall()
                    
                    for row in other_degrees:
                        target_degree_name = row[0]
                        target_degree_level = row[1]
                        
                        duplicate_params = (
                            based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                            sec_num, sec_term_context, sec_year_context, obj_code, 
                            target_degree_name, target_degree_level, course_num
                        )
                        target_where_params = duplicate_params[6:]
                        
                        target_exists = check_exists(cursor, target_where_params)
                        
                        if not target_exists:
                             cursor.execute(insert_query, duplicate_params)
                             saved_count += 1

        conn.commit()
        flash(f'Successfully saved and updated {saved_count} evaluation record(s)!', 'success')
        return redirect(url_for('evaluation.select_evaluation'))
    
    except Exception as e:
        conn.rollback()
        flash(f'FATAL SAVE ERROR: Evaluation failed to save. Details: {e}', 'error')
        return redirect(url_for('evaluation.select_evaluation'))

    finally:
        cursor.close()