#include <iostream>
#include <vector>
#include <fstream>
#include <sstream>
using namespace std;

class Student {
public:
    int id;
    string name;
    int age;
    string course;

    Student(int id, string name, int age, string course) {
        this->id = id;
        this->name = name;
        this->age = age;
        this->course = course;
    }

    void display() {
        cout << "ID: " << id << ", Name: " << name << ", Age: " << age << ", Course: " << course << endl;
    }
};

class StudentManager {
private:
    vector<Student> students;

public:
    void addStudent(int id, string name, int age, string course) {
        Student newStudent(id, name, age, course);
        students.push_back(newStudent);
        cout << "Student added successfully!\n";
    }

    void displayAll() {
        if (students.empty()) {
            cout << "No students to display.\n";
            return;
        }
        for (auto &student : students) {
            student.display();
        }
    }

    void searchStudent(int id) {
        for (auto &student : students) {
            if (student.id == id) {
                cout << "Student found:\n";
                student.display();
                return;
            }
        }
        cout << "Student not found.\n";
    }

    void deleteStudent(int id) {
        for (auto it = students.begin(); it != students.end(); ++it) {
            if (it->id == id) {
                students.erase(it);
                cout << "Student deleted successfully.\n";
                return;
            }
        }
        cout << "Student not found.\n";
    }

    void saveToFile(const string &filename) {
        ofstream file(filename);
        for (auto &student : students) {
            file << student.id << "," << student.name << "," << student.age << "," << student.course << endl;
        }
        file.close();
        cout << "Data saved to file.\n";
    }

    void loadFromFile(const string &filename) {
        ifstream file(filename);
        string line;
        while (getline(file, line)) {
            stringstream ss(line);
            string idStr, name, ageStr, course;
            getline(ss, idStr, ',');
            getline(ss, name, ',');
            getline(ss, ageStr, ',');
            getline(ss, course, ',');
            students.emplace_back(stoi(idStr), name, stoi(ageStr), course);
        }
        file.close();
        cout << "Data loaded from file.\n";
    }
};

int main() {
    StudentManager manager;
    int choice;

    do {
        cout << "\n--- Student Management System ---\n";
        cout << "1. Add Student\n2. Display All Students\n3. Search Student\n4. Delete Student\n5. Save to File\n6. Load from File\n0. Exit\n";
        cout << "Enter your choice: ";
        cin >> choice;

        if (choice == 1) {
            int id, age;
            string name, course;
            cout << "Enter ID: "; cin >> id;
            cout << "Enter Name: "; cin >> name;
            cout << "Enter Age: "; cin >> age;
            cout << "Enter Course: "; cin >> course;
            manager.addStudent(id, name, age, course);
        } else if (choice == 2) {
            manager.displayAll();
        } else if (choice == 3) {
            int id;
            cout << "Enter ID to search: ";
            cin >> id;
            manager.searchStudent(id);
        } else if (choice == 4) {
            int id;
            cout << "Enter ID to delete: ";
            cin >> id;
            manager.deleteStudent(id);
        } else if (choice == 5) {
            string filename;
            cout << "Enter filename to save: ";
            cin >> filename;
            manager.saveToFile(filename);
        } else if (choice == 6) {
            string filename;
            cout << "Enter filename to load: ";
            cin >> filename;
            manager.loadFromFile(filename);
        }
    } while (choice != 0);

    cout << "Exiting Student Management System. Goodbye!\n";
    return 0;
}
