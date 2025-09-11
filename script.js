// Task Board JavaScript
class TaskBoard {
    constructor() {
        this.socket = io();
        this.tasks = new Map();
        this.currentEditingTask = null;
        this.initializeEventListeners();
        this.initializeSocketEvents();
        this.showConnectionStatus();
    }

    initializeEventListeners() {
        // Add task button
        document.getElementById('addTaskBtn').addEventListener('click', () => {
            this.openTaskModal();
        });

        // Modal controls
        document.querySelector('.close').addEventListener('click', () => {
            this.closeTaskModal();
        });

        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.closeTaskModal();
        });

        // Task form submission
        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTask();
        });

        // Delete button
        document.getElementById('deleteBtn').addEventListener('click', () => {
            this.deleteTask();
        });

        // Search functionality
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.filterTasks(e.target.value);
        });

        // Assignee filter
        document.getElementById('filterAssignee').addEventListener('change', (e) => {
            this.filterByAssignee(e.target.value);
        });

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('taskModal');
            if (e.target === modal) {
                this.closeTaskModal();
            }
        });

        // Setup drag and drop for all columns
        this.setupDragAndDrop();
    }

    initializeSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus('connected');
            this.loadTasks();
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus('disconnected');
        });

        this.socket.on('tasksLoaded', (tasks) => {
            this.loadTasksFromServer(tasks);
        });

        this.socket.on('taskCreated', (task) => {
            this.addTaskToBoard(task);
            this.updateAssigneeFilter();
        });

        this.socket.on('taskUpdated', (task) => {
            this.updateTaskOnBoard(task);
            this.updateAssigneeFilter();
        });

        this.socket.on('taskDeleted', (taskId) => {
            this.removeTaskFromBoard(taskId);
            this.updateAssigneeFilter();
        });
    }

    showConnectionStatus() {
        const statusElement = document.createElement('div');
        statusElement.className = 'connection-status connecting';
        statusElement.textContent = 'Connecting...';
        statusElement.id = 'connectionStatus';
        document.body.appendChild(statusElement);
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
            statusElement.textContent = status === 'connected' ? 'Connected' : 
                                      status === 'disconnected' ? 'Disconnected' : 'Connecting...';
        }
    }

    loadTasks() {
        this.socket.emit('loadTasks');
    }

    loadTasksFromServer(tasks) {
        this.tasks.clear();
        this.clearBoard();
        
        tasks.forEach(task => {
            this.tasks.set(task.id, task);
            this.addTaskToBoard(task, false);
        });
        
        this.updateTaskCounts();
        this.updateAssigneeFilter();
    }

    openTaskModal(task = null) {
        const modal = document.getElementById('taskModal');
        const modalTitle = document.getElementById('modalTitle');
        const deleteBtn = document.getElementById('deleteBtn');
        const form = document.getElementById('taskForm');

        if (task) {
            modalTitle.textContent = 'Edit Task';
            deleteBtn.style.display = 'inline-block';
            this.currentEditingTask = task;
            this.populateForm(task);
        } else {
            modalTitle.textContent = 'Add New Task';
            deleteBtn.style.display = 'none';
            this.currentEditingTask = null;
            form.reset();
        }

        modal.style.display = 'block';
        document.getElementById('taskTitle').focus();
    }

    closeTaskModal() {
        const modal = document.getElementById('taskModal');
        modal.style.display = 'none';
        this.currentEditingTask = null;
        document.getElementById('taskForm').reset();
    }

    populateForm(task) {
        document.getElementById('taskTitle').value = task.title;
        document.getElementById('taskDescription').value = task.description || '';
        document.getElementById('taskAssignee').value = task.assignee || '';
        document.getElementById('taskDueDate').value = task.dueDate || '';
    }

    saveTask() {
        const title = document.getElementById('taskTitle').value.trim();
        const description = document.getElementById('taskDescription').value.trim();
        const assignee = document.getElementById('taskAssignee').value.trim();
        const dueDate = document.getElementById('taskDueDate').value;

        if (!title) {
            alert('Please enter a task title');
            return;
        }

        const taskData = {
            title,
            description,
            assignee,
            dueDate,
            status: this.currentEditingTask ? this.currentEditingTask.status : 'todo',
            createdAt: this.currentEditingTask ? this.currentEditingTask.createdAt : new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };

        if (this.currentEditingTask) {
            taskData.id = this.currentEditingTask.id;
            this.socket.emit('updateTask', taskData);
        } else {
            this.socket.emit('createTask', taskData);
        }

        this.closeTaskModal();
    }

    deleteTask() {
        if (this.currentEditingTask && confirm('Are you sure you want to delete this task?')) {
            this.socket.emit('deleteTask', this.currentEditingTask.id);
            this.closeTaskModal();
        }
    }

    addTaskToBoard(task, animate = true) {
        const taskElement = this.createTaskElement(task);
        const targetList = document.getElementById(`${task.status}-list`);
        
        if (animate) {
            taskElement.style.opacity = '0';
            taskElement.style.transform = 'translateY(-20px)';
        }
        
        targetList.appendChild(taskElement);
        
        if (animate) {
            setTimeout(() => {
                taskElement.style.transition = 'all 0.3s ease';
                taskElement.style.opacity = '1';
                taskElement.style.transform = 'translateY(0)';
            }, 10);
        }

        this.tasks.set(task.id, task);
        this.updateTaskCounts();
    }

    updateTaskOnBoard(task) {
        const existingElement = document.querySelector(`[data-task-id="${task.id}"]`);
        if (existingElement) {
            const newElement = this.createTaskElement(task);
            existingElement.parentNode.replaceChild(newElement, existingElement);
        }
        this.tasks.set(task.id, task);
        this.updateTaskCounts();
    }

    removeTaskFromBoard(taskId) {
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
        if (taskElement) {
            taskElement.style.transition = 'all 0.3s ease';
            taskElement.style.opacity = '0';
            taskElement.style.transform = 'translateX(-100%)';
            setTimeout(() => {
                taskElement.remove();
                this.updateTaskCounts();
            }, 300);
        }
        this.tasks.delete(taskId);
    }

    createTaskElement(task) {
        const div = document.createElement('div');
        div.className = 'task-card';
        div.setAttribute('data-task-id', task.id);
        div.draggable = true;

        const dueDate = task.dueDate ? new Date(task.dueDate) : null;
        const isOverdue = dueDate && dueDate < new Date() && task.status !== 'completed';
        
        div.innerHTML = `
            <h3>${this.escapeHtml(task.title)}</h3>
            ${task.description ? `<p>${this.escapeHtml(task.description)}</p>` : ''}
            <div class="task-meta">
                ${task.assignee ? `<span class="task-assignee">${this.escapeHtml(task.assignee)}</span>` : ''}
                ${task.dueDate ? `<span class="task-due-date ${isOverdue ? 'overdue' : ''}">${this.formatDate(task.dueDate)}</span>` : ''}
            </div>
        `;

        // Add click event to edit task
        div.addEventListener('click', (e) => {
            if (!e.target.closest('.task-meta')) {
                this.openTaskModal(task);
            }
        });

        // Add drag events
        this.addDragEvents(div);

        return div;
    }

    addDragEvents(element) {
        element.addEventListener('dragstart', (e) => {
            element.classList.add('dragging');
            e.dataTransfer.setData('text/plain', element.getAttribute('data-task-id'));
            e.dataTransfer.effectAllowed = 'move';
        });

        element.addEventListener('dragend', () => {
            element.classList.remove('dragging');
        });
    }

    setupDragAndDrop() {
        const taskLists = document.querySelectorAll('.task-list');
        
        taskLists.forEach(list => {
            list.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                list.classList.add('drag-over');
            });

            list.addEventListener('dragleave', (e) => {
                if (!list.contains(e.relatedTarget)) {
                    list.classList.remove('drag-over');
                }
            });

            list.addEventListener('drop', (e) => {
                e.preventDefault();
                list.classList.remove('drag-over');
                
                const taskId = e.dataTransfer.getData('text/plain');
                const newStatus = list.parentElement.getAttribute('data-status');
                
                this.moveTask(taskId, newStatus);
            });
        });
    }

    moveTask(taskId, newStatus) {
        const task = this.tasks.get(taskId);
        if (task && task.status !== newStatus) {
            const updatedTask = {
                ...task,
                status: newStatus,
                updatedAt: new Date().toISOString()
            };
            
            this.socket.emit('updateTask', updatedTask);
        }
    }

    filterTasks(searchTerm) {
        const tasks = document.querySelectorAll('.task-card');
        const term = searchTerm.toLowerCase();

        tasks.forEach(task => {
            const title = task.querySelector('h3').textContent.toLowerCase();
            const description = task.querySelector('p') ? task.querySelector('p').textContent.toLowerCase() : '';
            const assignee = task.querySelector('.task-assignee') ? task.querySelector('.task-assignee').textContent.toLowerCase() : '';
            
            const matches = title.includes(term) || description.includes(term) || assignee.includes(term);
            task.style.display = matches ? 'block' : 'none';
        });
    }

    filterByAssignee(assignee) {
        const tasks = document.querySelectorAll('.task-card');
        
        tasks.forEach(task => {
            const taskAssignee = task.querySelector('.task-assignee');
            const taskAssigneeName = taskAssignee ? taskAssignee.textContent : '';
            
            const matches = !assignee || taskAssigneeName === assignee;
            task.style.display = matches ? 'block' : 'none';
        });
    }

    updateAssigneeFilter() {
        const filter = document.getElementById('filterAssignee');
        const currentValue = filter.value;
        const assignees = new Set();
        
        this.tasks.forEach(task => {
            if (task.assignee) {
                assignees.add(task.assignee);
            }
        });
        
        // Clear existing options except "All Assignees"
        filter.innerHTML = '<option value="">All Assignees</option>';
        
        // Add assignee options
        Array.from(assignees).sort().forEach(assignee => {
            const option = document.createElement('option');
            option.value = assignee;
            option.textContent = assignee;
            filter.appendChild(option);
        });
        
        // Restore previous selection if it still exists
        if (currentValue && assignees.has(currentValue)) {
            filter.value = currentValue;
        }
    }

    updateTaskCounts() {
        const counts = { todo: 0, inprogress: 0, completed: 0 };
        
        this.tasks.forEach(task => {
            if (counts.hasOwnProperty(task.status)) {
                counts[task.status]++;
            }
        });
        
        Object.keys(counts).forEach(status => {
            const countElement = document.querySelector(`[data-status="${status}"] .task-count`);
            if (countElement) {
                countElement.textContent = counts[status];
            }
        });
    }

    clearBoard() {
        document.querySelectorAll('.task-list').forEach(list => {
            list.innerHTML = '';
        });
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the task board when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new TaskBoard();
});