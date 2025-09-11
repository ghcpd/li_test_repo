# Team Task Board

A real-time collaborative task management tool with drag-and-drop functionality, built with Node.js, Express, and Socket.IO.

![Task Board Screenshot](https://github.com/user-attachments/assets/8c048d12-a70d-4aba-8631-6d8b59c073c8)

## Features

### Core Functionality
- ✅ **Create, Edit, and Delete Tasks** - Full task lifecycle management
- ✅ **Drag-and-Drop Interface** - Move tasks between columns ("To Do" → "In Progress" → "Completed")
- ✅ **Real-time Synchronization** - All changes are instantly synced across all connected clients via WebSocket
- ✅ **Task Assignment** - Assign tasks to team members
- ✅ **Due Date Management** - Set and track task deadlines with overdue indicators
- ✅ **Task Descriptions** - Add detailed descriptions to tasks

### Interactive Features
- ✅ **Search Functionality** - Search tasks by title, description, or assignee
- ✅ **Filter by Assignee** - Filter tasks to show only specific team member's work
- ✅ **Live Task Counts** - Real-time count updates for each column
- ✅ **Connection Status** - Visual indicator showing WebSocket connection status
- ✅ **Responsive Design** - Works on desktop and mobile devices

### Technical Features
- ✅ **Real-time Updates** - WebSocket-based live synchronization
- ✅ **In-memory Storage** - Fast task storage (easily extendable to database)
- ✅ **RESTful Architecture** - Clean server-side API design
- ✅ **Modern UI/UX** - Clean, intuitive interface with smooth animations

## Screenshot

![Task Board with New Task](https://github.com/user-attachments/assets/efc2859c-2971-4530-be8d-f8a602465eb7)

## Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd li_test_repo
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the server**
   ```bash
   npm start
   ```

4. **Open in browser**
   Navigate to `http://localhost:3000`

### Usage

#### Creating Tasks
1. Click the **"+ Add Task"** button
2. Fill in the task details:
   - **Title** (required)
   - **Description** (optional)
   - **Assignee** (optional)
   - **Due Date** (optional)
3. Click **"Save Task"**

#### Moving Tasks
- **Drag and drop** tasks between columns to change their status
- Tasks will automatically sync across all connected clients

#### Searching and Filtering
- Use the **search box** to find tasks by title, description, or assignee
- Use the **assignee dropdown** to filter tasks by team member

#### Editing Tasks
- **Click on any task card** to edit its details
- Make changes and click **"Save Task"**
- Use the **"Delete"** button to remove tasks

## Architecture

### Frontend
- **HTML5** - Semantic markup structure
- **CSS3** - Modern styling with flexbox/grid, animations, and responsive design
- **Vanilla JavaScript** - Clean, dependency-free client-side code
- **Socket.IO Client** - Real-time communication

### Backend
- **Node.js** - Server runtime
- **Express.js** - Web server framework
- **Socket.IO** - WebSocket communication
- **UUID** - Unique task ID generation

### File Structure
```
li_test_repo/
├── index.html          # Main HTML page
├── styles.css          # CSS styling
├── script.js           # Frontend JavaScript
├── server.js           # Node.js server
├── package.json        # Dependencies and scripts
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## API Events (WebSocket)

### Client → Server
- `loadTasks` - Request all tasks
- `createTask` - Create a new task
- `updateTask` - Update existing task
- `deleteTask` - Delete a task

### Server → Client
- `tasksLoaded` - Send all tasks to client
- `taskCreated` - Broadcast new task to all clients
- `taskUpdated` - Broadcast task update to all clients
- `taskDeleted` - Broadcast task deletion to all clients

## Development

### Sample Data
The application starts with sample tasks to demonstrate functionality:
- **Setup project repository** (Completed - John Doe)
- **Design user interface mockups** (In Progress - Jane Smith)
- **Implement user authentication** (To Do - Mike Johnson)
- **Write API documentation** (To Do - Sarah Wilson)

### Extending the Application
- **Database Integration**: Replace in-memory storage with MongoDB, PostgreSQL, etc.
- **User Authentication**: Add login/logout functionality
- **File Attachments**: Allow file uploads on tasks
- **Comments**: Add task commenting system
- **Notifications**: Email/push notifications for task updates
- **Time Tracking**: Add time logging features
- **Labels/Tags**: Categorize tasks with labels

## Browser Compatibility
- **Modern browsers** supporting ES6, WebSocket, and CSS Grid
- **Tested on**: Chrome, Firefox, Safari, Edge

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License
ISC License - see package.json for details

---

**Built with ❤️ for team collaboration**