"""Lab 5, Part D warm-up: talk to a database from Python with the sqlite3 module.

Complete the four functions. Run the tests with:  pytest -q test_school_repo.py
Rule: ALWAYS use ? placeholders for values — never build SQL with + or f-strings.
"""
import sqlite3


def connect(path: str = "school.db") -> sqlite3.Connection:
    return sqlite3.connect(path)


def students_in_program(con: sqlite3.Connection, program: str) -> list[str]:
    """Names of students in `program`, sorted A→Z."""
    rows = con.execute("SELECT name FROM students WHERE program = ? ORDER BY name", (program,)).fetchall()
    return [r[0] for r in rows]                     # example — already done


def add_student(con: sqlite3.Connection, name: str, year: int, program: str) -> int:
    """Insert a student and return the new id."""
<<<<<<< HEAD
    # TODO D1: cur = con.execute("INSERT INTO students (name, year, program) VALUES (?, ?, ?)", (name, year, program))
    #          con.commit(); return cur.lastrowid
    raise NotImplementedError
=======
    cur = con.execute(
        "INSERT INTO students (name, year, program) VALUES (?, ?, ?)",
        (name, year, program),
    )
    con.commit()
    return int(cur.lastrowid)
>>>>>>> origin/main


def average_grade(con: sqlite3.Connection, course_code: str) -> float | None:
    """Average grade in a course (ignoring NULL), rounded to 2 decimals; None if no grades."""
<<<<<<< HEAD
    # TODO D2: SELECT AVG(grade) FROM enrollments WHERE course_code = ?   — then round, or return None
    raise NotImplementedError
=======
    row = con.execute(
        "SELECT AVG(grade) FROM enrollments WHERE course_code = ?",
        (course_code,),
    ).fetchone()
    if row is None or row[0] is None:
        return None
    return round(float(row[0]), 2)
>>>>>>> origin/main


def transcript(con: sqlite3.Connection, student_id: int) -> list[tuple[str, int, float | None]]:
    """(course title, credits, grade) for one student, sorted by title. Needs a JOIN."""
<<<<<<< HEAD
    # TODO D3: join enrollments with courses on course_code = code, filter by student_id, order by title
    raise NotImplementedError
=======
    rows = con.execute(
        """
        SELECT c.title, c.credits, e.grade
        FROM enrollments e
        JOIN courses c ON c.code = e.course_code
        WHERE e.student_id = ?
        ORDER BY c.title
        """,
        (student_id,),
    ).fetchall()
    return rows
>>>>>>> origin/main

