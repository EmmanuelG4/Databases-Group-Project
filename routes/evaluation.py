from flask import Blueprint, render_template, request, current_app, g
import mysql.connector

#create blueprint
evaluation_bp = Blueprint('evaluation', __name__)

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**current_app.config['DB_CONFIG'])
    return g.db

# selection pg
@evaluation_bp.route('/select', methods=['GET', 'POST'])
def select_evaluation():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # degrees for dropdown
    cursor.execute("SELECT degree_name, degree_level FROM degree")
    degrees = cursor.fetchall()

    # instructors for dropdown
    cursor.execute("SELECT instructor_id, instructor_name FROM instructor")
    instructors = cursor.fetchall()

    cursor.close()

    #render selection pg
    return render_template('eval_select.html', degrees=degrees, instructors=instructors)

# evaluations pg
@evaluation_bp.route('/enter', methods=['GET'])
def enter_evaluation():
    degree_combined = request.args.get('degree') # Comes in as "CS|MS"
    instructor_id = request.args.get('instructor_id')
    sec_term = request.args.get('sec_term')
    sec_year = request.args.get('sec_year')

#error check for missing data
    if not degree_combined or not instructor_id or not sec_term or not sec_year:
        return "Missing selection data", 400

#degree into name and lvl
    degree_name, degree_level = degree_combined.split('|')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # all sections taught by this instructor in this lvl
    query_sections = """
        SELECT T.sec_num, T.course_num, C.course_name
        FROM teaches T
        JOIN course C ON T.course_num = C.course_num
        WHERE T.instructor_id = %s AND T.sec_term = %s AND T.sec_year = %s
    """
    cursor.execute(query_sections, (instructor_id, sec_term, sec_year))
    sections = cursor.fetchall()

    # data structure
    sections_data = []

    for section in sections:
        # objectives linked to this course and degree
        query_objs = """
            SELECT L.obj_code, L.title, L.description
            FROM associated A
            JOIN learning_objective L ON A.obj_code = L.obj_code
            WHERE A.degree_name = %s AND A.degree_level = %s AND A.course_num = %s
        """
        cursor.execute(query_objs, (degree_name, degree_level, section['course_num']))
        objectives = cursor.fetchall()

        # for each obv check if evaliation exists
        objs_with_evals = []
        for obj in objectives:
            query_eval = """
                SELECT * FROM objective_eval
                WHERE sec_num = %s AND sec_term = %s AND sec_year = %s
                AND obj_code = %s AND degree_name = %s AND degree_level = %s
                AND course_num = %s
            """
            cursor.execute(query_eval, (
                section['sec_num'], sec_term, sec_year,
                obj['obj_code'], degree_name, degree_level,
                section['course_num']
            ))
            existing_eval = cursor.fetchone()

            objs_with_evals.append({
                'info': obj,
                'eval': existing_eval 
            })

        # add to main list
        sections_data.append({
            'meta': section,
            'objectives': objs_with_evals
        })

    cursor.close()
    
    # new entry pg
    return render_template('eval_entry.html', 
                           sections_data=sections_data,
                           degree_name=degree_name,
                           degree_level=degree_level,
                           instructor_id=instructor_id,
                           sec_term=sec_term,
                           sec_year=sec_year)

# save evals 
@evaluation_bp.route('/save', methods=['POST'])

@evaluation_bp.route('/save', methods=['POST'])
def save_evaluation():
    conn = get_db()
    cursor = conn.cursor()

    # grab context
    degree_name = request.form.get('degree_name')
    degree_level = request.form.get('degree_level')
    
    # loop through data
    for key, value in request.form.items():
        if '|' in key:
            parts = key.split('|')
            if len(parts) == 4:
                course_num, sec_num, obj_code, field = parts
                
                # only process based_on fields to avoid duplicates
                if field == 'based_on':
                    prefix = f"{course_num}|{sec_num}|{obj_code}|"
                    
                    # get nums 
                    based_on = value
                    perform_a = int(request.form.get(prefix + 'perform_a') or 0)
                    perform_b = int(request.form.get(prefix + 'perform_b') or 0)
                    perform_c = int(request.form.get(prefix + 'perform_c') or 0)
                    perform_f = int(request.form.get(prefix + 'perform_f') or 0)
                    improvements = request.form.get(prefix + 'improvements')

                    # check total students
                    sec_term = request.form.get('sec_term')
                    sec_year = request.form.get('sec_year')

                    # get limit from datasets
                    cursor.execute("SELECT num_students FROM section WHERE sec_num=%s AND course_num=%s AND sec_term=%s AND sec_year=%s", 
                                   (sec_num, course_num, sec_term, sec_year))
                    row = cursor.fetchone()
                    
                    if row:
                        limit = row[0] # max students 
                        total_entered = perform_a + perform_b + perform_c + perform_f
                        
                        if total_entered > limit:
                            return f"Error: You entered {total_entered} grades for Course {course_num}, but the section only has {limit} students! <a href='javascript:history.back()'>Go Back</a>"
                    

                    # check if exists
                    check_query = """
                        SELECT 1 FROM objective_eval
                        WHERE sec_num=%s AND sec_term=%s AND sec_year=%s 
                        AND obj_code=%s AND degree_name=%s AND degree_level=%s AND course_num=%s
                    """
                    cursor.execute(check_query, (sec_num, sec_term, sec_year, obj_code, degree_name, degree_level, course_num))
                    exists = cursor.fetchone()

                    if exists:
                        # update existing row
                        update_query = """
                            UPDATE objective_eval
                            SET based_on=%s, perform_a=%s, perform_b=%s, perform_c=%s, perform_f=%s, improvements=%s
                            WHERE sec_num=%s AND sec_term=%s AND sec_year=%s 
                            AND obj_code=%s AND degree_name=%s AND degree_level=%s AND course_num=%s
                        """
                        cursor.execute(update_query, (
                            based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                            sec_num, sec_term, sec_year, obj_code, degree_name, degree_level, course_num
                        ))
                    else:
                        # insert new row
                        insert_query = """
                            INSERT INTO objective_eval 
                            (based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                             sec_num, sec_term, sec_year, obj_code, degree_name, degree_level, course_num)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_query, (
                            based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                            sec_num, sec_term, sec_year, obj_code, degree_name, degree_level, course_num
                        ))

    conn.commit()
    cursor.close()

    return "Evaluations Saved Successfully! <a href='/evaluation/select'>Go Back</a>"