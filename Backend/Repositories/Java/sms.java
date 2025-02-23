import java.util.*;
import java.io.*;

class Student {
    private int id;
    private String name;
    private String course;
    private double gpa;

    public Student(int id, String name, String course, double gpa) {
        this.id = id;
        this.name = name;
        this.course = course;
        this.gpa = gpa;
    }

    public int getId() { return id; }
    public String getName() { return name; }
    public String getCourse() { return course; }
    public double getGpa() { return gpa; }

    public void display() {
        System.out.println("ID: " + id + ", Name: " + name + ", Course: " + course + ", GPA: " + gpa);
    }
}

class StudentManager {
    private List<Student> students = new ArrayList<>();

    public void addStudent(int id, String name, String course, double gpa) {
        students.add(new Student(id, name, course, gpa));
        System.out.println("Student added successfully!\n");
    }

    public void displayAll() {
        if (students.isEmpty()) {
            System.out.println("No students in the system.\n");
            return;
        }
        System.out.println("--- Student List ---");
        for (Student s : students) {
            s.display();
        }
    }

    public void searchStudent(int id) {
        for (Student s : students) {
            if (s.getId() == id) {
                System.out.println("Student found:");
                s.display();
                return;
            }
        }
        System.out.println("Student not found.\n");
    }

    public void deleteStudent(int id) {
        Iterator<Student> iterator = students.iterator();
        while (iterator.hasNext()) {
            if (iterator.next().getId() == id) {
                iterator.remove();
                System.out.println("Student deleted successfully.\n");
                return;
            }
        }
        System.out.println("Student not found.\n");
    }

    public void saveToFile(String filename) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(filename))) {
            for (Student s : students) {
                writer.write(s.getId() + "," + s.getName() + "," + s.getCourse() + "," + s.getGpa());
                writer.newLine();
            }
            System.out.println("Student data saved to file.\n");
        } catch (IOException e) {
            System.out.println("Error saving to file: " + e.getMessage());
        }
    }

    public void loadFromFile(String filename) {
        try (BufferedReader reader = new BufferedReader(new FileReader(filename))) {
            String line;
            students.clear();
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length == 4) {
                    int id = Integer.parseInt(parts[0]);
                    String name = parts[1];
                    String course = parts[2];
                    double gpa = Double.parseDouble(parts[3]);
                    students.add(new Student(id, name, course, gpa));
                }
            }
            System.out.println("Student data loaded from file.\n");
        } catch (IOException | NumberFormatException e) {
            System.out.println("Error loading from file: " + e.getMessage());
        }
    }
}

public class StudentManagementSystem {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        StudentManager manager = new StudentManager();
        int choice;

        do {
            System.out.println("\n--- Student Management System ---");
            System.out.println("1. Add Student\n2. Display All Students\n3. Search Student\n4. Delete Student\n5. Save to File\n6. Load from File\n0. Exit");
            System.out.print("Enter your choice: ");
            choice = scanner.nextInt();

            switch (choice) {
                case 1:
                    System.out.print("Enter ID: ");
                    int id = scanner.nextInt();
                    scanner.nextLine();
                    System.out.print("Enter Name: ");
                    String name = scanner.nextLine();
                    System.out.print("Enter Course: ");
                    String course = scanner.nextLine();
                    System.out.print("Enter GPA: ");
                    double gpa = scanner.nextDouble();
                    manager.addStudent(id, name, course, gpa);
                    break;
                case 2:
                    manager.displayAll();
                    break;
                case 3:
                    System.out.print("Enter ID to search: ");
                    int searchId = scanner.nextInt();
                    manager.searchStudent(searchId);
                    break;
                case 4:
                    System.out.print("Enter ID to delete: ");
                    int deleteId = scanner.nextInt();
                    manager.deleteStudent(deleteId);
                    break;
                case 5:
                    System.out.print("Enter filename to save: ");
                    scanner.nextLine();
                    String saveFile = scanner.nextLine();
                    manager.saveToFile(saveFile);
                    break;
                case 6:
                    System.out.print("Enter filename to load: ");
                    scanner.nextLine();
                    String loadFile = scanner.nextLine();
                    manager.loadFromFile(loadFile);
                    break;
                case 0:
                    System.out.println("Exiting Student Management System. Goodbye!");
                    break;
                default:
                    System.out.println("Invalid choice. Try again.\n");
            }
        } while (choice != 0);
        scanner.close();
    }
}
