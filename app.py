import os
from attendance_system import recognize_faces

while True:

    print("\n==============================")
    print(" SMART ATTENDANCE SYSTEM ")
    print("==============================")
    print("1. Start Attendance")
    print("2. Register Student")
    print("3. Encode Faces")
    print("4. View Attendance")
    print("5. Exit")

    choice = input("\nEnter Choice: ")

    if choice == "1":
        recognize_faces()

    elif choice == "2":
        os.system("python register_student.py")

    elif choice == "3":
        os.system("python encode_faces.py")

    elif choice == "4":
        os.system("python view_attendance.py")

    elif choice == "5":
        print("Thank You!")
        break

    else:
        print("Invalid Choice!")