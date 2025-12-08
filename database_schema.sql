CREATE DATABASE db_groupproj;
USE db_groupproj;

CREATE TABLE degree (
	degree_name VARCHAR(30),
    degree_level VARCHAR(5),
    PRIMARY KEY (degree_name, degree_level)
);

CREATE TABLE course (
	course_num VARCHAR(8) PRIMARY KEY,
	course_name VARCHAR(30)
);

CREATE TABLE requires (
	degree_name VARCHAR(30),
    degree_level VARCHAR(5),
    course_num VARCHAR (8),
    core BOOLEAN,
    PRIMARY KEY (degree_name, degree_level, course_num),
    FOREIGN KEY (degree_name, degree_level) REFERENCES degree(degree_name, degree_level),
    FOREIGN KEY (course_num) REFERENCES course(course_num)
);

CREATE TABLE section (
	sec_num VARCHAR(3),
    num_students INT,
    course_num VARCHAR (8),
    sec_term VARCHAR(6),
    sec_year YEAR,
	PRIMARY KEY (sec_num, course_num, sec_term, sec_year),
    FOREIGN KEY (course_num) REFERENCES course(course_num)
);

CREATE TABLE instructor (
	instructor_id VARCHAR(8) PRIMARY KEY,
    instructor_name VARCHAR(30)
);

CREATE TABLE teaches (
	sec_num VARCHAR(3),
    course_num VARCHAR (8),
    instructor_id VARCHAR(8),
    sec_term VARCHAR(6),
    sec_year YEAR,
    PRIMARY KEY (sec_num, course_num, instructor_id, sec_term, sec_year),
    FOREIGN KEY (sec_num, course_num, sec_term, sec_year) REFERENCES section(sec_num, course_num, sec_term, sec_year),
    FOREIGN KEY (instructor_id) REFERENCES instructor(instructor_id)
);

CREATE TABLE learning_objective (
	obj_code VARCHAR(8) PRIMARY KEY,
    title VARCHAR(120) UNIQUE,
    description TEXT
);

CREATE TABLE associated (
	degree_name VARCHAR(30),
    degree_level VARCHAR(5),
    course_num VARCHAR(8),
    obj_code VARCHAR(8),
    PRIMARY KEY (degree_name, degree_level, course_num, obj_code),
	FOREIGN KEY (degree_name, degree_level, course_num) REFERENCES requires(degree_name, degree_level, course_num),
    FOREIGN KEY (obj_code) REFERENCES learning_objective(obj_code)
);

CREATE TABLE objective_eval (
	based_on VARCHAR(30),
    perform_a INT,
    perform_b INT,
    perform_c INT,
    perform_f INT,
    improvements TEXT,
    sec_num VARCHAR(3), 
    sec_term VARCHAR(6),
    sec_year YEAR,
    obj_code VARCHAR(8),
    degree_name VARCHAR(30),
    degree_level VARCHAR(5),
    course_num VARCHAR(8),
    PRIMARY KEY (sec_num, sec_term, sec_year, obj_code, degree_name, degree_level, course_num),
    FOREIGN KEY (sec_num, course_num, sec_term, sec_year) REFERENCES section(sec_num, course_num, sec_term, sec_year),
    FOREIGN KEY (obj_code) REFERENCES learning_objective(obj_code),
    FOREIGN KEY (degree_name, degree_level) REFERENCES degree(degree_name, degree_level)
);