# Task Operations Guide - JavaScript/Node.js

Complete guide for performing CRUD operations on tasks in JavaScript and Node.js applications.

## Setup

```javascript
import TaskFlowClient from './client.js';
import logger from './logger.js';

class TaskService {
  constructor(client) {
    this.client = client;
  }
  
  // Task operations methods below
}

export default TaskService;
```

## Creating Tasks

### Simple Task Creation

```javascript
async function createSimpleTask(taskService) {
  const taskData = {
    title: 'Complete project documentation',
    description: 'Write comprehensive API documentation',
    priority: 'HIGH',
    status: 'TODO',
  };
  
  try {
    const result = await this.client.post('/api/tasks', taskData);
    logger.info(`Task created: ${result.id}`);
    return result;
  } catch (error) {
    logger.error(`Error creating task: ${error.message}`);
    throw error;
  }
}
```

### Task with Due Date

```javascript
async function createTaskWithDueDate() {
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + 7);
  
  const taskData = {
    title: 'Review pull requests',
    description: 'Review and approve pending pull requests',
    priority: 'MEDIUM',
    status: 'TODO',
    due_date: dueDate.toISOString(),
  };
  
  try {
    const result = await this.client.post('/api/tasks', taskData);
    logger.info(`Task created with due date: ${result.due_date}`);
    return result;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Task with Assignee

```javascript
async function createTaskWithAssignee(assigneeId) {
  const taskData = {
    title: 'Fix critical bug in authentication',
    description: 'Fix login issue on mobile devices',
    priority: 'HIGH',
    status: 'TODO',
    assigned_to: assigneeId,
  };
  
  try {
    const result = await this.client.post('/api/tasks', taskData);
    logger.info(`Task assigned to user ${result.assigned_to}`);
    return result;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Task with Tags

```javascript
async function createTaskWithTags(tags) {
  const taskData = {
    title: 'Implement caching layer',
    description: 'Add Redis caching for performance',
    priority: 'MEDIUM',
    status: 'TODO',
    tags,
  };
  
  try {
    const result = await this.client.post('/api/tasks', taskData);
    logger.info(`Task created with tags: ${JSON.stringify(result.tags)}`);
    return result;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

## Reading Tasks

### Get All Tasks

```javascript
async function getAllTasks() {
  try {
    const tasks = await this.client.get('/api/tasks');
    logger.info(`Retrieved ${tasks.length} tasks`);
    
    tasks.forEach(task => {
      console.log(`  [${task.id}] ${task.title} - ${task.status}`);
    });
    
    return tasks;
  } catch (error) {
    logger.error(`Error retrieving tasks: ${error.message}`);
    throw error;
  }
}
```

### Get Single Task

```javascript
async function getTaskById(taskId) {
  try {
    const task = await this.client.get(`/api/tasks/${taskId}`);
    logger.info(`Task: ${task.title}`);
    logger.info(`Priority: ${task.priority}, Status: ${task.status}`);
    return task;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Filter Tasks by Status

```javascript
async function getTasksByStatus(status) {
  try {
    const tasks = await this.client.get('/api/tasks', { 
      status 
    });
    logger.info(`Found ${tasks.length} tasks with status ${status}`);
    return tasks;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}

// Usage
const todoTasks = await getTasksByStatus('TODO');
const inProgressTasks = await getTasksByStatus('IN_PROGRESS');
```

### Filter Tasks by Priority

```javascript
async function getTasksByPriority(priority) {
  try {
    const tasks = await this.client.get('/api/tasks', { 
      priority 
    });
    logger.info(`Found ${tasks.length} ${priority} priority tasks`);
    return tasks;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Combined Filtering

```javascript
async function getFilteredTasks(filters = {}) {
  try {
    const tasks = await this.client.get('/api/tasks', filters);
    logger.info(`Found ${tasks.length} matching tasks`);
    return tasks;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}

// Usage
const tasks = await getFilteredTasks({
  status: 'TODO',
  priority: 'HIGH'
});
```

### Search Tasks

```javascript
async function searchTasks(query) {
  try {
    const tasks = await this.client.get('/api/tasks', { 
      search: query 
    });
    logger.info(`Found ${tasks.length} tasks matching "${query}"`);
    
    tasks.forEach(task => {
      console.log(`  - ${task.title}`);
    });
    
    return tasks;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

## Updating Tasks

### Update Task Status

```javascript
async function updateTaskStatus(taskId, newStatus) {
  try {
    const result = await this.client.put(
      `/api/tasks/${taskId}`,
      { status: newStatus }
    );
    logger.info(`Task status updated to: ${result.status}`);
    return result;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Update Task Priority

```javascript
async function updateTaskPriority(taskId, newPriority) {
  try {
    const result = await this.client.put(
      `/api/tasks/${taskId}`,
      { priority: newPriority }
    );
    logger.info(`Task priority updated to: ${result.priority}`);
    return result;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Update Multiple Fields

```javascript
async function updateTaskFull(taskId, updates) {
  try {
    const result = await this.client.put(
      `/api/tasks/${taskId}`,
      updates
    );
    logger.info('Task updated successfully');
    return result;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}

// Usage
const updated = await updateTaskFull(1, {
  title: 'Updated Title',
  description: 'Updated description',
  status: 'IN_PROGRESS',
  priority: 'HIGH'
});
```

### Mark Task as Complete

```javascript
async function completeTask(taskId) {
  try {
    const result = await this.client.put(
      `/api/tasks/${taskId}`,
      {
        status: 'COMPLETED',
        completed_at: new Date().toISOString(),
      }
    );
    logger.info('Task marked as completed');
    return result;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

## Deleting Tasks

### Delete Single Task

```javascript
async function deleteTask(taskId) {
  try {
    const result = await this.client.delete(`/api/tasks/${taskId}`);
    logger.info(`Task ${taskId} deleted successfully`);
    return result;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Delete with Confirmation

```javascript
async function deleteTaskWithConfirmation(taskId) {
  try {
    const task = await getTaskById(taskId);
    
    // In Node.js, use readline for confirmation
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    return new Promise((resolve) => {
      rl.question(`Delete task "${task.title}"? (yes/no): `, async (answer) => {
        rl.close();
        
        if (answer.toLowerCase() === 'yes') {
          const result = await this.client.delete(`/api/tasks/${taskId}`);
          logger.info('Task deleted');
          resolve(result);
        } else {
          logger.info('Deletion cancelled');
          resolve(null);
        }
      });
    });
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

## Batch Operations

### Batch Create Tasks

```javascript
async function batchCreateTasks(tasksData) {
  const created = [];
  const failed = [];
  
  for (let i = 0; i < tasksData.length; i++) {
    try {
      const result = await this.client.post('/api/tasks', tasksData[i]);
      created.push(result);
      logger.info(`[${i + 1}/${tasksData.length}] Created: ${result.title}`);
    } catch (error) {
      failed.push({ task: tasksData[i], error: error.message });
      logger.error(`[${i + 1}/${tasksData.length}] Failed: ${error.message}`);
    }
  }
  
  logger.info(`Summary: ${created.length} created, ${failed.length} failed`);
  return { created, failed };
}

// Usage
const tasksToCreate = [
  { title: 'Task 1', priority: 'HIGH' },
  { title: 'Task 2', priority: 'MEDIUM' },
  { title: 'Task 3', priority: 'LOW' },
];

const results = await batchCreateTasks(tasksToCreate);
```

### Batch Update Tasks

```javascript
async function batchUpdateTasks(taskUpdates) {
  const updated = [];
  const failed = [];
  
  for (const [taskId, updateData] of Object.entries(taskUpdates)) {
    try {
      const result = await this.client.put(
        `/api/tasks/${taskId}`,
        updateData
      );
      updated.push(result);
      logger.info(`Updated task ${taskId}`);
    } catch (error) {
      failed.push({ taskId, error: error.message });
      logger.error(`Failed to update task ${taskId}: ${error.message}`);
    }
  }
  
  return { updated, failed };
}

// Usage
const updates = {
  1: { status: 'IN_PROGRESS' },
  2: { priority: 'HIGH' },
  3: { status: 'COMPLETED' },
};

const results = await batchUpdateTasks(updates);
```

### Bulk Status Update

```javascript
async function bulkUpdateStatus(taskIds, newStatus) {
  let updated = 0;
  
  for (const taskId of taskIds) {
    try {
      await this.client.put(`/api/tasks/${taskId}`, { status: newStatus });
      updated++;
    } catch (error) {
      logger.error(`Failed to update task ${taskId}: ${error.message}`);
    }
  }
  
  logger.info(`Updated ${updated}/${taskIds.length} tasks to ${newStatus}`);
  return updated;
}

// Usage
const taskIds = [1, 2, 3, 4, 5];
await bulkUpdateStatus(taskIds, 'IN_PROGRESS');
```

## Advanced Patterns

### Task Workflow Pipeline

```javascript
async function moveTaskThroughWorkflow(taskId) {
  const workflowStates = ['TODO', 'IN_PROGRESS', 'REVIEW', 'COMPLETED'];
  
  try {
    const task = await getTaskById(taskId);
    const currentState = task.status;
    
    const currentIndex = workflowStates.indexOf(currentState);
    if (currentIndex >= 0 && currentIndex < workflowStates.length - 1) {
      const nextState = workflowStates[currentIndex + 1];
      const result = await updateTaskStatus(taskId, nextState);
      logger.info(`Task moved: ${currentState} -> ${nextState}`);
      return result;
    } else {
      logger.info('Task already completed');
      return null;
    }
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Task Statistics

```javascript
async function getTaskStatistics() {
  try {
    const tasks = await getAllTasks();
    
    const stats = {
      total: tasks.length,
      by_status: {},
      by_priority: {},
    };
    
    for (const task of tasks) {
      stats.by_status[task.status] = (stats.by_status[task.status] || 0) + 1;
      stats.by_priority[task.priority] = (stats.by_priority[task.priority] || 0) + 1;
    }
    
    logger.info(`Total tasks: ${stats.total}`);
    logger.info(`By status: ${JSON.stringify(stats.by_status)}`);
    logger.info(`By priority: ${JSON.stringify(stats.by_priority)}`);
    
    return stats;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

### Overdue Task Alert

```javascript
async function findOverdueTasks() {
  try {
    const tasks = await getAllTasks();
    const now = new Date();
    
    const overdue = tasks.filter(task => {
      if (task.due_date && task.status !== 'COMPLETED') {
        const dueDate = new Date(task.due_date);
        return dueDate < now;
      }
      return false;
    });
    
    logger.info(`Found ${overdue.length} overdue tasks:`);
    overdue.forEach(task => {
      console.log(`  - ${task.title} (due: ${task.due_date})`);
    });
    
    return overdue;
  } catch (error) {
    logger.error(`Error: ${error.message}`);
    throw error;
  }
}
```

## Express.js Integration

### Express Middleware for Task Service

```javascript
import express from 'express';
import TaskService from './task-service.js';
import TaskFlowClient from './client.js';

const app = express();
app.use(express.json());

const taskFlowClient = new TaskFlowClient();
const taskService = new TaskService(taskFlowClient);

// Get all tasks
app.get('/tasks', async (req, res) => {
  try {
    const tasks = await taskService.getAllTasks();
    res.json(tasks);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create task
app.post('/tasks', async (req, res) => {
  try {
    const task = await taskService.createSimpleTask(req.body);
    res.status(201).json(task);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Update task
app.put('/tasks/:id', async (req, res) => {
  try {
    const task = await taskService.updateTaskFull(req.params.id, req.body);
    res.json(task);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Delete task
app.delete('/tasks/:id', async (req, res) => {
  try {
    await taskService.deleteTask(req.params.id);
    res.json({ message: 'Task deleted' });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

## Next Steps

- Explore [Task Filtering Guide](./TASK_FILTERING_GUIDE.md)
- Check [Advanced Features](../advanced-features/)
- Review [Testing Integration Guide](../best-practices/TESTING_INTEGRATION_GUIDE.md)