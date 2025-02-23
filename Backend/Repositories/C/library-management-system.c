#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_TITLE 100
#define MAX_AUTHOR 100
#define MAX_BOOKS 1000

typedef struct {
    int id;
    char title[MAX_TITLE];
    char author[MAX_AUTHOR];
    int year;
} Book;

Book library[MAX_BOOKS];
int book_count = 0;

void addBook() {
    if (book_count >= MAX_BOOKS) {
        printf("Library is full!\n");
        return;
    }
    Book newBook;
    newBook.id = book_count + 1;

    printf("Enter book title: ");
    getchar();
    fgets(newBook.title, MAX_TITLE, stdin);
    newBook.title[strcspn(newBook.title, "\n")] = '\0';

    printf("Enter author name: ");
    fgets(newBook.author, MAX_AUTHOR, stdin);
    newBook.author[strcspn(newBook.author, "\n")] = '\0';

    printf("Enter publication year: ");
    scanf("%d", &newBook.year);

    library[book_count++] = newBook;
    printf("Book added successfully!\n");
}

void displayBooks() {
    if (book_count == 0) {
        printf("No books in the library.\n");
        return;
    }
    printf("\n--- Library Books ---\n");
    for (int i = 0; i < book_count; i++) {
        printf("ID: %d | Title: %s | Author: %s | Year: %d\n",
               library[i].id, library[i].title, library[i].author, library[i].year);
    }
}

void searchBook() {
    char title[MAX_TITLE];
    printf("Enter book title to search: ");
    getchar();
    fgets(title, MAX_TITLE, stdin);
    title[strcspn(title, "\n")] = '\0';

    for (int i = 0; i < book_count; i++) {
        if (strcasecmp(library[i].title, title) == 0) {
            printf("Book found: ID: %d | Title: %s | Author: %s | Year: %d\n",
                   library[i].id, library[i].title, library[i].author, library[i].year);
            return;
        }
    }
    printf("Book not found.\n");
}

void deleteBook() {
    int id;
    printf("Enter book ID to delete: ");
    scanf("%d", &id);

    int found = 0;
    for (int i = 0; i < book_count; i++) {
        if (library[i].id == id) {
            for (int j = i; j < book_count - 1; j++) {
                library[j] = library[j + 1];
            }
            book_count--;
            printf("Book deleted successfully.\n");
            found = 1;
            break;
        }
    }
    if (!found) {
        printf("Book not found.\n");
    }
}

void saveToFile(const char *filename) {
    FILE *file = fopen(filename, "w");
    if (!file) {
        printf("Error opening file for writing.\n");
        return;
    }
    for (int i = 0; i < book_count; i++) {
        fprintf(file, "%d,%s,%s,%d\n", library[i].id, library[i].title, library[i].author, library[i].year);
    }
    fclose(file);
    printf("Library saved to file.\n");
}

void loadFromFile(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        printf("Error opening file for reading.\n");
        return;
    }
    book_count = 0;
    while (fscanf(file, "%d,%99[^,],%99[^,],%d\n", &library[book_count].id, library[book_count].title,
                  library[book_count].author, &library[book_count].year) == 4) {
        book_count++;
    }
    fclose(file);
    printf("Library loaded from file.\n");
}

int main() {
    int choice;
    char filename[100] = "library_data.txt";

    do {
        printf("\n--- Library Management System ---\n");
        printf("1. Add Book\n2. Display All Books\n3. Search Book\n4. Delete Book\n5. Save to File\n6. Load from File\n0. Exit\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch (choice) {
            case 1:
                addBook();
                break;
            case 2:
                displayBooks();
                break;
            case 3:
                searchBook();
                break;
            case 4:
                deleteBook();
                break;
            case 5:
                saveToFile(filename);
                break;
            case 6:
                loadFromFile(filename);
                break;
            case 0:
                printf("Exiting Library Management System. Goodbye!\n");
                break;
            default:
                printf("Invalid choice. Try again.\n");
        }
    } while (choice != 0);

    return 0;
}
