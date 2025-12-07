from db import get_connection


def add_degree():
    name = input("Degree name (e.g., Computer Science): ")
    level = input("Level (BA, BS, MS, PhD, Cert): ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO degree (degree_name, degree_level) VALUES (%s, %s)",
        (name, level)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Degree added.\n")



def add_course():
    course_num = input("Course number (e.g., CSE2340): ")
    course_name = input("Course name/title: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO course (course_num, course_name) VALUES (%s, %s)",
        (course_num, course_name)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Course added.\n")



def add_instructor():
    instr_id = input("Instructor ID (string, e.g. INST001): ")
    instr_name = input("Instructor name: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO instructor (instructor_id, instructor_name) VALUES (%s, %s)",
        (instr_id, instr_name)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Instructor added.\n")


def add_section():
    sec_num = input("Section number (e.g., 001): ")
    num_students = int(input("Number of students: "))
    course_num = input("Course number (must exist in course table): ")
    sec_term = input("Term (Fall/Spring/Summer): ")
    sec_year = int(input("Year (e.g., 2025): "))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """INSERT INTO section 
           (sec_num, num_students, course_num, sec_term, sec_year)
           VALUES (%s, %s, %s, %s, %s)""",
        (sec_num, num_students, course_num, sec_term, sec_year)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Section added.\n")



def add_objective():
    obj_code = input("Objective code (e.g., LO1): ")
    title = input("Title (<=120 chars): ")
    description = input("Description: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """INSERT INTO learning_objective (obj_code, title, description)
           VALUES (%s, %s, %s)""",
        (obj_code, title, description)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Learning objective added.\n")


def link_course_objective():
    degree_name = input("Degree name: ")
    degree_level = input("Degree level (BA/BS/MS/etc.): ")
    course_num = input("Course number: ")
    obj_code = input("Objective code: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """INSERT INTO associated (degree_name, degree_level, course_num, obj_code)
           VALUES (%s, %s, %s, %s)""",
        (degree_name, degree_level, course_num, obj_code)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Objective linked to course.\n")


# ------------------------
# MAIN MENU
# ------------------------
def main_menu():
    while True:
        print("=== Data Entry Menu ===")
        print("1. Add Degree")
        print("2. Add Course")
        print("3. Add Instructor")
        print("4. Add Section")
        print("5. Add Objective")
        print("6. Link Course to Objective")
        print("0. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_degree()
        elif choice == "2":
            add_course()
        elif choice == "3":
            add_instructor()
        elif choice == "4":
            add_section()
        elif choice == "5":
            add_objective()
        elif choice == "6":
            link_course_objective()
        elif choice == "0":
            break
        else:
            print("Invalid option.\n")


if __name__ == "__main__":
    main_menu()