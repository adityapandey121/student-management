students = []


def add_student():
    student_id = input("Enter student ID: ").strip()
    name = input("Enter student name: ").strip()
    course = input("Enter course: ").strip()

    if not student_id or not name or not course:
        print("All fields are required.")
        return

    if any(student["id"] == student_id for student in students):
        print("Student ID already exists.")
        return

    students.append({"id": student_id, "name": name, "course": course})
    print("Student added successfully!")


def view_students():
    if not students:
        print("No students found.")
        return

    print("\n--- Student List ---")
    for student in students:
        print(
            f'ID: {student["id"]} | '
            f'Name: {student["name"]} | '
            f'Course: {student["course"]}'
        )


def search_student():
    student_id = input("Enter student ID to search: ").strip()
    for student in students:
        if student["id"] == student_id:
            print("Student found:", student)
            return
    print("Student not found.")


def delete_student():
    student_id = input("Enter student ID to delete: ").strip()
    for student in students:
        if student["id"] == student_id:
            students.remove(student)
            print("Student deleted successfully!")
            return
    print("Student not found.")


def count_students():
    print(f"Total students: {len(students)}")


def main():
    while True:
        print("\n=== Student Management System ===")
        print("1. Add student")
        print("2. View students")
        print("3. Search student")
        print("4. Delete student")
        print("5. Count students")
        print("6. Exit")

        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_student()
        elif choice == "2":
            view_students()
        elif choice == "3":
            search_student()
        elif choice == "4":
            delete_student()
        elif choice == "5":
            count_students()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
