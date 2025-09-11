(() => {
  const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host);

  const state = {
    tasks: new Map(),
    filter: { title: '', assignee: '', due: '' },
    editingId: null,
  };

  const els = {
    lists: {
      todo: document.getElementById('todo'),
      inprogress: document.getElementById('inprogress'),
      completed: document.getElementById('completed'),
    },
    search: document.getElementById('searchInput'),
    assignee: document.getElementById('assigneeFilter'),
    due: document.getElementById('dueFilter'),
    clearFilters: document.getElementById('clearFilters'),
    newTaskBtn: document.getElementById('newTaskBtn'),
    modal: document.getElementById('modal'),
    modalTitle: document.getElementById('modalTitle'),
    title: document.getElementById('taskTitle'),
    desc: document.getElementById('taskDesc'),
    dueInput: document.getElementById('taskDue'),
    assigneeInput: document.getElementById('taskAssignee'),
    saveBtn: document.getElementById('saveTask'),
    deleteBtn: document.getElementById('deleteTask'),
    cancelBtn: document.getElementById('cancelTask'),
  };

  function openModal(task) {
    els.modal.classList.remove('hidden');
    if (task) {
      els.modalTitle.textContent = 'Edit Task';
      state.editingId = task.id;
      els.title.value = task.title;
      els.desc.value = task.description;
      els.dueInput.value = task.dueDate;
      els.assigneeInput.value = task.assignee;
      els.deleteBtn.classList.remove('hidden');
    } else {
      els.modalTitle.textContent = 'New Task';
      state.editingId = null;
      els.title.value = '';
      els.desc.value = '';
      els.dueInput.value = '';
      els.assigneeInput.value = '';
      els.deleteBtn.classList.add('hidden');
    }
  }

  function closeModal() {
    els.modal.classList.add('hidden');
  }

  function matchesFilter(task) {
    const t = state.filter.title.toLowerCase();
    const a = state.filter.assignee.toLowerCase();
    const d = state.filter.due;
    return (
      (!t || task.title.toLowerCase().includes(t)) &&
      (!a || (task.assignee || '').toLowerCase().includes(a)) &&
      (!d || task.dueDate === d)
    );
  }

  function render() {
    Object.values(els.lists).forEach((el) => (el.innerHTML = ''));
    Array.from(state.tasks.values()).forEach((task) => {
      if (!matchesFilter(task)) return;
      const card = document.createElement('div');
      card.className = 'task';
      card.draggable = true;
      card.dataset.id = task.id;
      card.innerHTML = `
        <h4>${task.title || '(No title)'}</h4>
        <p>${task.description || ''}</p>
        <div class="meta">
          <span>👤 ${task.assignee || '-'}</span>
          <span>📅 ${task.dueDate || '-'}</span>
        </div>
      `;

      card.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', task.id);
      });

      card.addEventListener('dblclick', () => {
        openModal(task);
      });

      const list = els.lists[task.status] || els.lists.todo;
      list.appendChild(card);
    });
  }

  function send(msg) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    } else {
      ws.addEventListener('open', () => ws.send(JSON.stringify(msg)), { once: true });
    }
  }

  // Drag and drop handling for lists
  Object.entries(els.lists).forEach(([status, listEl]) => {
    listEl.addEventListener('dragover', (e) => {
      e.preventDefault();
      listEl.classList.add('drag-over');
    });
    listEl.addEventListener('dragleave', () => listEl.classList.remove('drag-over'));
    listEl.addEventListener('drop', (e) => {
      e.preventDefault();
      listEl.classList.remove('drag-over');
      const id = e.dataTransfer.getData('text/plain');
      if (!id) return;
      const task = state.tasks.get(id);
      if (!task || task.status === status) return;
      send({ type: 'move', id, status });
    });
  });

  // Filters
  els.search.addEventListener('input', (e) => {
    state.filter.title = e.target.value;
    render();
  });
  els.assignee.addEventListener('input', (e) => {
    state.filter.assignee = e.target.value;
    render();
  });
  els.due.addEventListener('change', (e) => {
    state.filter.due = e.target.value;
    render();
  });
  els.clearFilters.addEventListener('click', () => {
    state.filter = { title: '', assignee: '', due: '' };
    els.search.value = '';
    els.assignee.value = '';
    els.due.value = '';
    render();
  });

  // Modal buttons
  els.newTaskBtn.addEventListener('click', () => openModal());
  els.cancelBtn.addEventListener('click', () => closeModal());
  els.saveBtn.addEventListener('click', () => {
    const payload = {
      title: els.title.value.trim(),
      description: els.desc.value.trim(),
      dueDate: els.dueInput.value,
      assignee: els.assigneeInput.value.trim(),
      status: 'todo',
    };

    if (state.editingId) {
      send({ type: 'update', task: { id: state.editingId, ...payload } });
    } else {
      send({ type: 'create', task: payload });
    }
    closeModal();
  });

  els.deleteBtn.addEventListener('click', () => {
    if (state.editingId) {
      send({ type: 'delete', id: state.editingId });
    }
    closeModal();
  });

  // WebSocket events
  ws.addEventListener('message', (ev) => {
    try {
      const data = JSON.parse(ev.data);
      if (data.type === 'init') {
        state.tasks.clear();
        (data.tasks || []).forEach((t) => state.tasks.set(t.id, t));
        render();
      } else if (data.type === 'created' || data.type === 'updated') {
        state.tasks.set(data.task.id, data.task);
        render();
      } else if (data.type === 'deleted') {
        state.tasks.delete(data.id);
        render();
      } else if (data.type === 'moved') {
        const task = state.tasks.get(data.id);
        if (task) {
          task.status = data.status;
          state.tasks.set(task.id, task);
          render();
        }
      }
    } catch (_e) {
      // ignore
    }
  });
})();
