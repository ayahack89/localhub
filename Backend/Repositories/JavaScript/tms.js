// Task Management System

class Task {
     constructor(id, title, description, completed = false) {
         this.id = id;
         this.title = title;
         this.description = description;
         this.completed = completed;
     }
 }
 
 class TaskManager {
     constructor() {
         this.tasks = JSON.parse(localStorage.getItem('tasks')) || [];
     }
 
     addTask(title, description) {
         const id = Date.now();
         const task = new Task(id, title, description);
         this.tasks.push(task);
         this.saveTasks();
         this.displayTasks();
     }
 
     deleteTask(id) {
         this.tasks = this.tasks.filter(task => task.id !== id);
         this.saveTasks();
         this.displayTasks();
     }
 
     toggleComplete(id) {
         const task = this.tasks.find(task => task.id === id);
         if (task) {
             task.completed = !task.completed;
             this.saveTasks();
             this.displayTasks();
         }
     }
 
     saveTasks() {
         localStorage.setItem('tasks', JSON.stringify(this.tasks));
     }
 
     displayTasks() {
         const taskList = document.getElementById('task-list');
         taskList.innerHTML = '';
 
         this.tasks.forEach(task => {
             const taskItem = document.createElement('li');
             taskItem.className = `task-item ${task.completed ? 'completed' : ''}`;
 
             taskItem.innerHTML = `
                 <h3>${task.title}</h3>
                 <p>${task.description}</p>
                 <button onclick="taskManager.toggleComplete(${task.id})">${task.completed ? 'Undo' : 'Complete'}</button>
                 <button onclick="taskManager.deleteTask(${task.id})">Delete</button>
             `;
 
             taskList.appendChild(taskItem);
         });
     }
 }
 
 const taskManager = new TaskManager();
 document.addEventListener('DOMContentLoaded', () => taskManager.displayTasks());
 
 // Event Listeners
 document.getElementById('task-form').addEventListener('submit', (e) => {
     e.preventDefault();
     const title = document.getElementById('task-title').value;
     const description = document.getElementById('task-desc').value;
 
     if (title && description) {
         taskManager.addTask(title, description);
         document.getElementById('task-form').reset();
     }
 });
 