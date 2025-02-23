<?php
// Database connection
$host = 'localhost';
$user = 'root';
$password = '';
$dbname = 'blog_system';

$conn = new mysqli($host, $user, $password, $dbname);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Create table if not exists
$sql = "CREATE TABLE IF NOT EXISTS posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)";

$conn->query($sql);

// Handle form submissions
if (isset($_POST['action'])) {
    $action = $_POST['action'];
    $title = $_POST['title'] ?? '';
    $content = $_POST['content'] ?? '';
    $id = $_POST['id'] ?? '';

    if ($action == 'create') {
        $stmt = $conn->prepare("INSERT INTO posts (title, content) VALUES (?, ?)");
        $stmt->bind_param("ss", $title, $content);
        $stmt->execute();
    } elseif ($action == 'update') {
        $stmt = $conn->prepare("UPDATE posts SET title=?, content=? WHERE id=?");
        $stmt->bind_param("ssi", $title, $content, $id);
        $stmt->execute();
    } elseif ($action == 'delete') {
        $stmt = $conn->prepare("DELETE FROM posts WHERE id=?");
        $stmt->bind_param("i", $id);
        $stmt->execute();
    }
}

// Fetch all posts
$result = $conn->query("SELECT * FROM posts ORDER BY created_at DESC");
?>

<!DOCTYPE html>
<html>
<head>
    <title>Blog Management System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .post { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        .form-group { margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>Blog Management System</h1>

    <h2>Create New Post</h2>
    <form method="POST">
        <div class="form-group">
            <label>Title:</label><br>
            <input type="text" name="title" required>
        </div>
        <div class="form-group">
            <label>Content:</label><br>
            <textarea name="content" rows="5" cols="40" required></textarea>
        </div>
        <input type="hidden" name="action" value="create">
        <button type="submit">Create Post</button>
    </form>

    <h2>All Posts</h2>
    <?php while($row = $result->fetch_assoc()): ?>
        <div class="post">
            <h3><?php echo htmlspecialchars($row['title']); ?></h3>
            <p><?php echo nl2br(htmlspecialchars($row['content'])); ?></p>
            <small>Posted on: <?php echo $row['created_at']; ?></small>
            <form method="POST" style="display:inline;">
                <input type="hidden" name="id" value="<?php echo $row['id']; ?>">
                <input type="hidden" name="action" value="delete">
                <button type="submit">Delete</button>
            </form>
        </div>
    <?php endwhile; ?>

</body>
</html>

<?php $conn->close(); ?>
