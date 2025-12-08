from flask import Blueprint, render_template, request, flash, redirect, url_for
from database.handler import execute_query, get_db_connection_for_request


evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation', template_folder='../templates')


@evaluation_bp.route('/', methods=['GET'])
@evaluation_bp.route('/select', methods=['GET'])
def select_evaluation():
    """Step 1: Let the instructor pick degree, instructor, and semester."""
    try:
        degrees = execute_query(
            "SELECT degree_name, degree_level FROM degree ORDER BY degree_name"
        )
        instructors = execute_query(
            "SELECT instructor_id, instructor_name FROM instructor ORDER BY instructor_name"
        )

        terms = ['Fall', 'Spring', 'Summer']

        return render_template(
            'evaluation/eval_select.html',
            degrees=degrees,
            instructors=instructors,
            terms=terms
        )
    except Exception as e:
        flash(f'Error loading dropdowns: {e}', 'error')
        return redirect(url_for('index'))


@evaluation_bp.route('/list_sections', methods=['GET'])
def list_sections_status():
    """Show all sections taught that semester and whether their objectives are entered."""
    
    degree_combined = request.args.get('degree')
    instructor_id = request.args.get('instructor_id')
    sec_term = request.args.get('sec_term')
    sec_year = request.args.get('sec_year')

    if not all([degree_combined, instructor_id, sec_term, sec_year]):
        flash("Please fill out all fields first.", 'error')
        return redirect(url_for('evaluation.select_evaluation'))

    degree_name, degree_level = degree_combined.split('|')

    query_sections = """
        SELECT S.sec_num, S.course_num, S.sec_term, S.sec_year,
               C.course_name, S.num_students
        FROM teaches T
        JOIN section S
          ON T.sec_num = S.sec_num
         AND T.course_num = S.course_num
         AND T.sec_term = S.sec_term
         AND T.sec_year = S.sec_year
        JOIN course C ON S.course_num = C.course_num
        WHERE T.instructor_id = %s
          AND T.sec_term = %s
          AND T.sec_year = %s
    """

    sections = execute_query(
        query_sections,
        (instructor_id, sec_term, sec_year)
    )

    sections_data = []

    for section in sections:
        course_num = section['course_num']

        query_objs = """
            SELECT L.obj_code, L.title
            FROM associated A
            JOIN learning_objective L ON A.obj_code = L.obj_code
            WHERE A.degree_name = %s
              AND A.degree_level = %s
              AND A.course_num = %s
        """
        objectives = execute_query(query_objs, (degree_name, degree_level, course_num))

        eval_count = 0

        for obj in objectives:
            check_query = """
                SELECT
                    based_on,
                    perform_a,
                    perform_b,
                    perform_c,
                    perform_f,
                    improvements
                FROM objective_eval
                WHERE sec_num=%s AND sec_term=%s AND sec_year=%s
                AND obj_code=%s
                AND degree_name=%s AND degree_level=%s
                AND course_num=%s
            """

            eval_row = execute_query(
                check_query,
                (
                    section['sec_num'], sec_term, sec_year,
                    obj['obj_code'], degree_name, degree_level, course_num
                ),
                fetch_one=True
            )

            if eval_row:
                    obj['status'] = 'Entered'
                    obj['improvement_entered'] = bool(eval_row.get('improvements'))
                    obj['based_on'] = eval_row['based_on']
                    obj['perform_a'] = eval_row['perform_a']
                    obj['perform_b'] = eval_row['perform_b']
                    obj['perform_c'] = eval_row['perform_c']
                    obj['perform_f'] = eval_row['perform_f']
                    obj['improvements'] = eval_row['improvements']

                    eval_count += 1
            else:
                    obj['status'] = 'Missing'
                    obj['improvement_entered'] = False



        total = len(objectives)
        if total == 0:
            status = "Not Entered"
        elif eval_count == total:
            status = "Fully Entered"
        elif eval_count > 0:
            status = f"Partially Entered ({eval_count}/{total})"
        else:
            status = "Not Entered"

        sections_data.append({
            'section': section,
            'objectives': objectives,
            'status': status
        })

    return render_template(
        'evaluation/eval_entry.html',
        sections_data=sections_data,
        context={
            'degree_name': degree_name,
            'degree_level': degree_level,
            'instructor_id': instructor_id,
            'sec_term': sec_term,
            'sec_year': sec_year
        }
    )


@evaluation_bp.route('/save', methods=['POST'])
def save_evaluation():
    """Save all evaluation data entered on the big form."""

    def check_exists(cursor, pk_params):
        """Check whether this objective_eval row already exists."""
        check_query = """
            SELECT 1 FROM objective_eval
            WHERE sec_num=%s AND sec_term=%s AND sec_year=%s
              AND obj_code=%s
              AND degree_name=%s AND degree_level=%s
              AND course_num=%s
        """
        cursor.execute(check_query, pk_params)
        return cursor.fetchone()

    conn = get_db_connection_for_request()
    cursor = conn.cursor()

    degree_name_context = request.form.get('degree_name')
    degree_level_context = request.form.get('degree_level')
    sec_term_context = request.form.get('sec_term')
    sec_year_context = request.form.get('sec_year')

    saved_count = 0

    try:
        for key, value in request.form.items():
            if "|" in key and key.endswith("|based_on"):
                course_num, sec_num, obj_code, _ = key.split("|")
                prefix = f"{course_num}|{sec_num}|{obj_code}|"

                based_on = value
                perform_a = int(request.form.get(prefix + 'perform_a') or 0)
                perform_b = int(request.form.get(prefix + 'perform_b') or 0)
                perform_c = int(request.form.get(prefix + 'perform_c') or 0)
                perform_f = int(request.form.get(prefix + 'perform_f') or 0)
                improvements = request.form.get(prefix + 'improvements')
                
               #make sure not too many
                total_entered = perform_a + perform_b + perform_c + perform_f

                cursor.execute(
                    "SELECT num_students FROM section WHERE course_num=%s AND sec_num=%s AND sec_term=%s AND sec_year=%s",
                    (course_num, sec_num, sec_term_context, sec_year_context)
                )
                student_limit_row = cursor.fetchone()
                
                if student_limit_row:
                    max_students = student_limit_row[0]
                    
                    if total_entered != max_students:
                        flash(f"Error: You entered {total_entered} grades for Course {course_num} (Section {sec_num}), but the class limit is {max_students}.", "error")
                        return redirect(url_for('evaluation.select_evaluation'))

                eval_params = (
                    based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                    sec_num, sec_term_context, sec_year_context,
                    obj_code, degree_name_context, degree_level_context, course_num
                )

                pk_params = eval_params[6:]  # primary key fields

                exists = check_exists(cursor, pk_params)

                if exists:
                    update_sql = """
                        UPDATE objective_eval
                        SET based_on=%s, perform_a=%s, perform_b=%s,
                            perform_c=%s, perform_f=%s, improvements=%s
                        WHERE sec_num=%s AND sec_term=%s AND sec_year=%s
                          AND obj_code=%s AND degree_name=%s AND degree_level=%s
                          AND course_num=%s
                    """
                    cursor.execute(update_sql, eval_params)
                else:
                    insert_sql = """
                        INSERT INTO objective_eval
                          (based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                           sec_num, sec_term, sec_year,
                           obj_code, degree_name, degree_level, course_num)
                        VALUES (%s, %s, %s, %s, %s, %s,
                                %s, %s, %s,
                                %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, eval_params)

                saved_count += 1

                duplicate_key = f"{prefix}duplicate"
                if request.form.get(duplicate_key) == 'on':
                    query_other = """
                        SELECT DISTINCT degree_name, degree_level
                        FROM associated
                        WHERE course_num=%s AND obj_code=%s
                        AND NOT (degree_name=%s AND degree_level=%s)
                    """
                    cursor.execute(
                        query_other,
                        (course_num, obj_code, degree_name_context, degree_level_context)
                    )

                    for dn, dl in cursor.fetchall():
                        dup_params = (
                            based_on, perform_a, perform_b, perform_c, perform_f, improvements,
                            sec_num, sec_term_context, sec_year_context,
                            obj_code, dn, dl, course_num
                        )
                        dup_pk = dup_params[6:]

                        if not check_exists(cursor, dup_pk):
                            cursor.execute(insert_sql, dup_params)
                            saved_count += 1

        conn.commit()
        flash(f"Saved {saved_count} evaluation record(s).", "success")
        return redirect(url_for('evaluation.select_evaluation'))

    except Exception as e:
        conn.rollback()
        flash(f"Error saving evaluations: {e}", "error")
        return redirect(url_for('evaluation.select_evaluation'))
    finally:
        cursor.close()
