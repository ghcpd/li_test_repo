const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// In-memory task storage (in production, use a database)
let tasks = new Map();

// Serve static files
app.use(express.static(path.join(__dirname)));

// Main route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Socket.IO connection handling
io.on('connection', (socket) => {
    console.log('User connected:', socket.id);

    // Send welcome message
    socket.emit('connected', { message: 'Connected to Task Board' });

    // Load all tasks for the client
    socket.on('loadTasks', () => {
        const taskArray = Array.from(tasks.values());
        socket.emit('tasksLoaded', taskArray);
    });

    // Create a new task
    socket.on('createTask', (taskData) => {
        try {
            const task = {
                id: uuidv4(),
                title: taskData.title,
                description: taskData.description || '',
                assignee: taskData.assignee || '',
                dueDate: taskData.dueDate || '',
                status: taskData.status || 'todo',
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };

            tasks.set(task.id, task);
            
            // Broadcast to all clients
            io.emit('taskCreated', task);
            
            console.log('Task created:', task.title);
        } catch (error) {
            console.error('Error creating task:', error);
            socket.emit('error', { message: 'Failed to create task' });
        }
    });

    // Update an existing task
    socket.on('updateTask', (taskData) => {
        try {
            if (!taskData.id) {
                socket.emit('error', { message: 'Task ID is required for update' });
                return;
            }

            const existingTask = tasks.get(taskData.id);
            if (!existingTask) {
                socket.emit('error', { message: 'Task not found' });
                return;
            }

            const updatedTask = {
                ...existingTask,
                title: taskData.title,
                description: taskData.description || '',
                assignee: taskData.assignee || '',
                dueDate: taskData.dueDate || '',
                status: taskData.status,
                updatedAt: new Date().toISOString()
            };

            tasks.set(updatedTask.id, updatedTask);
            
            // Broadcast to all clients
            io.emit('taskUpdated', updatedTask);
            
            console.log('Task updated:', updatedTask.title);
        } catch (error) {
            console.error('Error updating task:', error);
            socket.emit('error', { message: 'Failed to update task' });
        }
    });

    // Delete a task
    socket.on('deleteTask', (taskId) => {
        try {
            if (!taskId) {
                socket.emit('error', { message: 'Task ID is required for deletion' });
                return;
            }

            const task = tasks.get(taskId);
            if (!task) {
                socket.emit('error', { message: 'Task not found' });
                return;
            }

            tasks.delete(taskId);
            
            // Broadcast to all clients
            io.emit('taskDeleted', taskId);
            
            console.log('Task deleted:', task.title);
        } catch (error) {
            console.error('Error deleting task:', error);
            socket.emit('error', { message: 'Failed to delete task' });
        }
    });

    // Get task statistics
    socket.on('getStats', () => {
        try {
            const stats = {
                total: tasks.size,
                todo: 0,
                inprogress: 0,
                completed: 0,
                assignees: new Set()
            };

            tasks.forEach(task => {
                if (task.status === 'todo') stats.todo++;
                else if (task.status === 'inprogress') stats.inprogress++;
                else if (task.status === 'completed') stats.completed++;
                
                if (task.assignee) stats.assignees.add(task.assignee);
            });

            stats.assignees = Array.from(stats.assignees);
            socket.emit('statsUpdated', stats);
        } catch (error) {
            console.error('Error getting stats:', error);
            socket.emit('error', { message: 'Failed to get statistics' });
        }
    });

    // Handle client disconnect
    socket.on('disconnect', (reason) => {
        console.log('User disconnected:', socket.id, 'Reason:', reason);
    });

    // Handle errors
    socket.on('error', (error) => {
        console.error('Socket error for client', socket.id, ':', error);
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Express error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

// Initialize with some sample tasks for demonstration
function initializeSampleTasks() {
    const sampleTasks = [
        {
            id: uuidv4(),
            title: 'Setup project repository',
            description: 'Create GitHub repository and initialize with basic project structure',
            assignee: 'John Doe',
            dueDate: '2025-01-15',
            status: 'completed',
            createdAt: new Date(Date.now() - 86400000 * 3).toISOString(),
            updatedAt: new Date(Date.now() - 86400000 * 1).toISOString()
        },
        {
            id: uuidv4(),
            title: 'Design user interface mockups',
            description: 'Create wireframes and mockups for the main application screens',
            assignee: 'Jane Smith',
            dueDate: '2025-01-20',
            status: 'inprogress',
            createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
            updatedAt: new Date(Date.now() - 86400000 * 0.5).toISOString()
        },
        {
            id: uuidv4(),
            title: 'Implement user authentication',
            description: 'Add login/logout functionality with secure session management',
            assignee: 'Mike Johnson',
            dueDate: '2025-01-25',
            status: 'todo',
            createdAt: new Date(Date.now() - 86400000 * 1).toISOString(),
            updatedAt: new Date(Date.now() - 86400000 * 1).toISOString()
        },
        {
            id: uuidv4(),
            title: 'Write API documentation',
            description: 'Document all REST API endpoints with examples and response formats',
            assignee: 'Sarah Wilson',
            dueDate: '2025-01-30',
            status: 'todo',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        }
    ];

    sampleTasks.forEach(task => {
        tasks.set(task.id, task);
    });
    
    console.log(`Initialized with ${sampleTasks.length} sample tasks`);
}

// Start the server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Task Board server running on port ${PORT}`);
    console.log(`Open http://localhost:${PORT} in your browser`);
    
    // Initialize sample tasks
    initializeSampleTasks();
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('SIGINT received, shutting down gracefully');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});