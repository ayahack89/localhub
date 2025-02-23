using System;
using System.Collections.Generic;
using System.IO;

class Item
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int Quantity { get; set; }
    public double Price { get; set; }

    public Item(int id, string name, int quantity, double price)
    {
        Id = id;
        Name = name;
        Quantity = quantity;
        Price = price;
    }

    public void Display()
    {
        Console.WriteLine($"ID: {Id}, Name: {Name}, Quantity: {Quantity}, Price: ${Price}");
    }
}

class InventoryManager
{
    private List<Item> inventory = new List<Item>();

    public void AddItem(int id, string name, int quantity, double price)
    {
        inventory.Add(new Item(id, name, quantity, price));
        Console.WriteLine("Item added successfully!\n");
    }

    public void DisplayAll()
    {
        if (inventory.Count == 0)
        {
            Console.WriteLine("No items in inventory.\n");
            return;
        }
        Console.WriteLine("--- Inventory List ---");
        foreach (var item in inventory)
        {
            item.Display();
        }
    }

    public void SearchItem(int id)
    {
        foreach (var item in inventory)
        {
            if (item.Id == id)
            {
                Console.WriteLine("Item found:");
                item.Display();
                return;
            }
        }
        Console.WriteLine("Item not found.\n");
    }

    public void DeleteItem(int id)
    {
        var item = inventory.Find(i => i.Id == id);
        if (item != null)
        {
            inventory.Remove(item);
            Console.WriteLine("Item deleted successfully.\n");
        }
        else
        {
            Console.WriteLine("Item not found.\n");
        }
    }

    public void SaveToFile(string filename)
    {
        using (StreamWriter writer = new StreamWriter(filename))
        {
            foreach (var item in inventory)
            {
                writer.WriteLine($"{item.Id},{item.Name},{item.Quantity},{item.Price}");
            }
        }
        Console.WriteLine("Inventory saved to file.\n");
    }

    public void LoadFromFile(string filename)
    {
        if (!File.Exists(filename))
        {
            Console.WriteLine("File not found.\n");
            return;
        }
        inventory.Clear();
        var lines = File.ReadAllLines(filename);
        foreach (var line in lines)
        {
            var parts = line.Split(',');
            if (parts.Length == 4)
            {
                int id = int.Parse(parts[0]);
                string name = parts[1];
                int quantity = int.Parse(parts[2]);
                double price = double.Parse(parts[3]);
                inventory.Add(new Item(id, name, quantity, price));
            }
        }
        Console.WriteLine("Inventory loaded from file.\n");
    }
}

class Program
{
    static void Main(string[] args)
    {
        InventoryManager manager = new InventoryManager();
        int choice;

        do
        {
            Console.WriteLine("\n--- Inventory Management System ---");
            Console.WriteLine("1. Add Item\n2. Display All Items\n3. Search Item\n4. Delete Item\n5. Save to File\n6. Load from File\n0. Exit");
            Console.Write("Enter your choice: ");
            choice = int.Parse(Console.ReadLine());

            switch (choice)
            {
                case 1:
                    Console.Write("Enter ID: ");
                    int id = int.Parse(Console.ReadLine());
                    Console.Write("Enter Name: ");
                    string name = Console.ReadLine();
                    Console.Write("Enter Quantity: ");
                    int quantity = int.Parse(Console.ReadLine());
                    Console.Write("Enter Price: ");
                    double price = double.Parse(Console.ReadLine());
                    manager.AddItem(id, name, quantity, price);
                    break;
                case 2:
                    manager.DisplayAll();
                    break;
                case 3:
                    Console.Write("Enter ID to search: ");
                    int searchId = int.Parse(Console.ReadLine());
                    manager.SearchItem(searchId);
                    break;
                case 4:
                    Console.Write("Enter ID to delete: ");
                    int deleteId = int.Parse(Console.ReadLine());
                    manager.DeleteItem(deleteId);
                    break;
                case 5:
                    Console.Write("Enter filename to save: ");
                    string saveFile = Console.ReadLine();
                    manager.SaveToFile(saveFile);
                    break;
                case 6:
                    Console.Write("Enter filename to load: ");
                    string loadFile = Console.ReadLine();
                    manager.LoadFromFile(loadFile);
                    break;
                case 0:
                    Console.WriteLine("Exiting Inventory Management System. Goodbye!");
                    break;
                default:
                    Console.WriteLine("Invalid choice. Try again.\n");
                    break;
            }
        } while (choice != 0);
    }
}
