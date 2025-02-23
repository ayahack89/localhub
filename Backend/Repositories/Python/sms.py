import sqlite3

# Initialize database
def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            grade TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Add new student
def add_student(name, age, grade):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO students (name, age, grade) VALUES (?, ?, ?)', (name, age, grade))
    conn.commit()
    conn.close()
    print(f"Student {name} added successfully.")

# View all students
def view_students():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    conn.close()
    if students:
        print("\nID | Name       | Age | Grade")
        print("-------------------------------")
        for student in students:
            print(f"{student[0]:<3} | {student[1]:<10} | {student[2]:<3} | {student[3]}")
    else:
        print("No students found.")

# Update student
def update_student(student_id, name, age, grade):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE students SET name = ?, age = ?, grade = ? WHERE id = ?', (name, age, grade, student_id))
    conn.commit()
    conn.close()
    print(f"Student ID {student_id} updated successfully.")

# Delete student
def delete_student(student_id):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    print(f"Student ID {student_id} deleted successfully.")

# Main menu
def main():
    init_db()
    while True:
        print("\n--- Student Management System ---")
        print("1. Add Student")
        print("2. View Students")
        print("3. Update Student")
        print("4. Delete Student")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            name = input("Enter student name: ")
            age = int(input("Enter student age: "))
            grade = input("Enter student grade: ")
            add_student(name, age, grade)

        elif choice == '2':
            view_students()

        elif choice == '3':
            student_id = int(input("Enter student ID to update: "))
            name = input("Enter new name: ")
            age = int(input("Enter new age: "))
            grade = input("Enter new grade: ")
            update_student(student_id, name, age, grade)

        elif choice == '4':
            student_id = int(input("Enter student ID to delete: "))
            delete_student(student_id)

        elif choice == '5':
            print("Exiting... Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
