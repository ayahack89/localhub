use serde::{Deserialize, Serialize};
use std::fs::{File, OpenOptions};
use std::io::{self, BufReader, BufWriter, Write};
use std::path::Path;

#[derive(Serialize, Deserialize, Debug)]
struct Task {
    id: u32,
    description: String,
    completed: bool,
}

impl Task {
    fn new(id: u32, description: String) -> Self {
        Task {
            id,
            description,
            completed: false,
        }
    }
}

fn main() {
    let mut tasks = load_tasks("tasks.json").unwrap_or_else(|_| Vec::new());
    let mut next_id = tasks.len() as u32 + 1;

    loop {
        println!("\n--- To-Do List ---");
        println!("1. Add Task");
        println!("2. Display Tasks");
        println!("3. Complete Task");
        println!("4. Delete Task");
        println!("5. Save and Exit");
        println!("Enter your choice:");

        let mut choice = String::new();
        io::stdin().read_line(&mut choice).unwrap();
        match choice.trim() {
            "1" => {
                println!("Enter task description:");
                let mut desc = String::new();
                io::stdin().read_line(&mut desc).unwrap();
                tasks.push(Task::new(next_id, desc.trim().to_string()));
                next_id += 1;
                println!("Task added!");
            }
            "2" => display_tasks(&tasks),
            "3" => {
                println!("Enter task ID to complete:");
                let mut id_str = String::new();
                io::stdin().read_line(&mut id_str).unwrap();
                if let Ok(id) = id_str.trim().parse::<u32>() {
                    if let Some(task) = tasks.iter_mut().find(|t| t.id == id) {
                        task.completed = true;
                        println!("Task marked as completed.");
                    } else {
                        println!("Task not found.");
                    }
                } else {
                    println!("Invalid ID.");
                }
            }
            "4" => {
                println!("Enter task ID to delete:");
                let mut id_str = String::new();
                io::stdin().read_line(&mut id_str).unwrap();
                if let Ok(id) = id_str.trim().parse::<u32>() {
                    let len_before = tasks.len();
                    tasks.retain(|t| t.id != id);
                    if tasks.len() < len_before {
                        println!("Task deleted.");
                    } else {
                        println!("Task not found.");
                    }
                } else {
                    println!("Invalid ID.");
                }
            }
            "5" => {
                save_tasks("tasks.json", &tasks).expect("Failed to save tasks.");
                println!("Tasks saved. Goodbye!");
                break;
            }
            _ => println!("Invalid choice, try again."),
        }
    }
}

fn display_tasks(tasks: &[Task]) {
    if tasks.is_empty() {
        println!("No tasks found.");
    } else {
        println!("\nCurrent Tasks:");
        for task in tasks {
            println!(
                "ID: {} | [{}] {}",
                task.id,
                if task.completed { "x" } else { " " },
                task.description
            );
        }
    }
}

fn load_tasks<P: AsRef<Path>>(path: P) -> Result<Vec<Task>, io::Error> {
    if !path.as_ref().exists() {
        return Ok(Vec::new());
    }
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let tasks = serde_json::from_reader(reader).unwrap_or_else(|_| Vec::new());
    Ok(tasks)
}

fn save_tasks<P: AsRef<Path>>(path: P, tasks: &[Task]) -> Result<(), io::Error> {
    let file = OpenOptions::new().write(true).create(true).truncate(true).open(path)?;
    let writer = BufWriter::new(file);
    serde_json::to_writer_pretty(writer, tasks).expect("Failed to write tasks.");
    Ok(())
}
