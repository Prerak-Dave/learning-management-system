// ============================================================
// Config
// ============================================================
const API = 'http://127.0.0.1:8000';

// ============================================================
// State
// ============================================================
let accessToken = localStorage.getItem('access') || '';
let refreshToken = localStorage.getItem('refresh') || '';
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

// ============================================================
// Helpers
// ============================================================
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
}

function showError(elId, msg) {
  const el = document.getElementById(elId);
  el.textContent = msg;
  el.style.display = 'block';
}

function hideError(elId) {
  const el = document.getElementById(elId);
  el.style.display = 'none';
}

function showSuccess(elId, msg) {
  const el = document.getElementById(elId);
  el.textContent = msg;
  el.style.display = 'block';
}

async function apiFetch(path, options = {}) {
  options.headers = options.headers || {};
  if (accessToken) options.headers['Authorization'] = 'Bearer ' + accessToken;
  if (!(options.body instanceof FormData)) {
    options.headers['Content-Type'] = 'application/json';
  }
  let res = await fetch(API + path, options);

  // Try refresh if 401
  if (res.status === 401 && refreshToken) {
    const ref = await fetch(API + '/auth/login/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });
    if (ref.ok) {
      const data = await ref.json();
      accessToken = data.access;
      localStorage.setItem('access', accessToken);
      options.headers['Authorization'] = 'Bearer ' + accessToken;
      res = await fetch(API + path, options);
    } else {
      doLogout();
      return null;
    }
  }
  return res;
}

function setActive(linkId) {
  document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
  const el = document.getElementById(linkId);
  if (el) el.classList.add('active');
}

// ============================================================
// Auth
// ============================================================
async function doLogin() {
  hideError('login-error');
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  const roleEl = document.querySelector('input[name="login-role"]:checked');

  if (!username || !password) return showError('login-error', 'Please fill in username and password.');
  if (!roleEl) return showError('login-error', 'Please select a role.');

  const res = await fetch(API + '/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, role: parseInt(roleEl.value) })
  });
  const data = await res.json();
  if (!res.ok || data.detail || data.non_field_errors) {
    return showError('login-error', data.detail || data.non_field_errors || JSON.stringify(data));
  }
  accessToken = data.access;
  refreshToken = data.refresh;
  localStorage.setItem('access', accessToken);
  localStorage.setItem('refresh', refreshToken);

  currentUser = {
    username,
    role: roleEl.value === '1' ? 'student' : 'mentor',
    roleId: parseInt(roleEl.value)
  };
  localStorage.setItem('currentUser', JSON.stringify(currentUser));
  loadApp();
}

async function doSignup() {
  hideError('signup-error');
  hideError('signup-success');
  const username = document.getElementById('signup-username').value.trim();
  const email = document.getElementById('signup-email').value.trim();
  const password = document.getElementById('signup-password').value;
  const password2 = document.getElementById('signup-password2').value;
  const role = document.getElementById('signup-role').value;

  if (!username || !email || !password || !password2 || !role) {
    return showError('signup-error', 'Please fill in all fields.');
  }
  if (password !== password2) return showError('signup-error', 'Passwords do not match.');

  const res = await fetch(API + '/auth/signup/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password, password2, role: [parseInt(role)] })
  });
  const data = await res.json();
  if (data.response === 'User successfully created') {
    showSuccess('signup-success', 'Account created! You can now log in.');
    document.getElementById('signup-username').value = '';
    document.getElementById('signup-email').value = '';
    document.getElementById('signup-password').value = '';
    document.getElementById('signup-password2').value = '';
    document.getElementById('signup-role').value = '';
  } else {
    showError('signup-error', JSON.stringify(data));
  }
}

async function doLogout() {
  if (refreshToken) {
    await fetch(API + '/auth/logout/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + accessToken },
      body: JSON.stringify({ refresh: refreshToken })
    }).catch(() => {});
  }
  accessToken = ''; refreshToken = '';
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
  localStorage.removeItem('currentUser');
  currentUser = null;
  showPage('page-login');
}

// ============================================================
// App bootstrap
// ============================================================
function loadApp() {
  document.getElementById('user-info').textContent =
    currentUser.username + ' (' + currentUser.role + ')';
  buildSidebar();
  showPage('page-app');
}

function buildSidebar() {
  const sidebar = document.getElementById('sidebar');
  const isMentor = currentUser.role === 'mentor';
  sidebar.innerHTML = '';

  const links = isMentor ? [
    { id: 'nav-courses', label: 'All Courses', fn: 'loadCourses' },
    { id: 'nav-my-courses', label: 'My Courses', fn: 'loadMyCourses' },
    { id: 'nav-create-course', label: 'Create Course', fn: 'loadCreateCourse' },
    { id: 'nav-topics', label: 'Topics', fn: 'loadTopics' },
    { id: 'nav-assignments', label: 'Assignments', fn: 'loadAssignments' },
    { id: 'nav-submissions', label: 'Submissions', fn: 'loadSubmissions' },
  ] : [
    { id: 'nav-courses', label: 'Browse Courses', fn: 'loadCourses' },
    { id: 'nav-enrollments', label: 'My Enrollments', fn: 'loadEnrollments' },
    { id: 'nav-topics', label: 'My Topics', fn: 'loadTopics' },
    { id: 'nav-assignments', label: 'Assignments', fn: 'loadAssignments' },
    { id: 'nav-submissions', label: 'My Submissions', fn: 'loadSubmissions' },
    { id: 'nav-submit', label: 'Submit Assignment', fn: 'loadSubmitForm' },
  ];

  links.forEach(l => {
    const a = document.createElement('a');
    a.id = l.id;
    a.href = '#';
    a.textContent = l.label;
    a.onclick = (e) => { e.preventDefault(); window[l.fn](); };
    sidebar.appendChild(a);
  });
}

function setContent(html) {
  document.getElementById('main-content').innerHTML = html;
}

// ============================================================
// Courses
// ============================================================
async function loadCourses() {
  setActive('nav-courses');
  setContent('<h3>All Courses</h3><p class="section-msg">Loading...</p>');
  const res = await apiFetch('/courses/');
  const data = await res.json();

  const isMentor = currentUser.role === 'mentor';
  let rows = data.map(c => `
    <tr>
      <td>${c.id}</td>
      <td>${c.title}</td>
      <td>${c.description}</td>
      <td>${c.start_date}</td>
      ${!isMentor ? `<td><button class="btn-action" onclick="enroll(${c.id})">Enroll</button></td>` : ''}
    </tr>`).join('');

  setContent(`
    <h3>All Courses</h3>
    <table>
      <thead><tr><th>ID</th><th>Title</th><th>Description</th><th>Start Date</th>${!isMentor ? '<th>Action</th>' : ''}</tr></thead>
      <tbody>${rows || '<tr><td colspan="5" class="section-msg">No courses found.</td></tr>'}</tbody>
    </table>`);
}

async function loadMyCourses() {
  setActive('nav-my-courses');
  setContent('<h3>My Courses</h3><p class="section-msg">Loading...</p>');
  const res = await apiFetch('/courses/?creator=' + currentUser.username);
  // The filter uses user ID; let's just load all and note mentor can use create course
  // Actually fetch all; DRF filterset_fields=["creator"] expects pk
  // We'll show all courses from the list view that we own by checking creator_username in detail view
  // Simpler: fetch all courses detail -- but list returns basic fields.
  // Solution: fetch all and show them (mentor sees their courses via filterset but we need their user id)
  // We'll just show all courses with a note
  const data = await res.json();
  let rows = data.map(c => `
    <tr>
      <td>${c.id}</td>
      <td>${c.title}</td>
      <td>${c.description}</td>
      <td>${c.start_date}</td>
      <td>
        <button class="btn-action" onclick="showEditCourse(${c.id}, '${escHtml(c.title)}', '${escHtml(c.description)}')">Edit</button>
        <button class="btn-danger" style="margin-left:5px" onclick="deleteCourse(${c.id})">Delete</button>
      </td>
    </tr>`).join('');

  setContent(`
    <h3>My Courses</h3>
    <p class="section-msg" style="margin-bottom:10px">Note: Showing all courses. Only courses you created can be edited/deleted.</p>
    <table>
      <thead><tr><th>ID</th><th>Title</th><th>Description</th><th>Start Date</th><th>Actions</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="5" class="section-msg">No courses found.</td></tr>'}</tbody>
    </table>
    <div id="edit-course-box"></div>`);
}

async function loadCreateCourse() {
  setActive('nav-create-course');
  setContent(`
    <h3>Create Course</h3>
    <div class="form-box">
      <div id="create-course-error" class="error-msg"></div>
      <div id="create-course-success" class="success-msg"></div>
      <label>Title</label>
      <input type="text" id="cc-title" placeholder="Course title" />
      <label>Description</label>
      <textarea id="cc-desc" placeholder="Course description"></textarea>
      <button onclick="createCourse()">Create Course</button>
    </div>`);
}

async function createCourse() {
  hideError('create-course-error');
  const title = document.getElementById('cc-title').value.trim();
  const description = document.getElementById('cc-desc').value.trim();
  if (!title || !description) return showError('create-course-error', 'Please fill in all fields.');

  const res = await apiFetch('/courses/', {
    method: 'POST',
    body: JSON.stringify({ title, description })
  });
  const data = await res.json();
  if (res.ok) {
    showSuccess('create-course-success', 'Course created successfully! ID: ' + data.id);
    document.getElementById('cc-title').value = '';
    document.getElementById('cc-desc').value = '';
  } else {
    showError('create-course-error', JSON.stringify(data));
  }
}

async function deleteCourse(id) {
  if (!confirm('Delete course #' + id + '?')) return;
  const res = await apiFetch('/courses/' + id + '/', { method: 'DELETE' });
  if (res.ok || res.status === 204) {
    alert('Deleted.');
    loadMyCourses();
  } else {
    const data = await res.json();
    alert(JSON.stringify(data));
  }
}

function showEditCourse(id, title, desc) {
  document.getElementById('edit-course-box').innerHTML = `
    <div class="form-box" style="margin-top:20px">
      <h4>Edit Course #${id}</h4>
      <div id="edit-course-error" class="error-msg"></div>
      <div id="edit-course-success" class="success-msg"></div>
      <label>Title</label>
      <input type="text" id="ec-title" value="${escHtml(title)}" />
      <label>Description</label>
      <textarea id="ec-desc">${escHtml(desc)}</textarea>
      <button onclick="updateCourse(${id})">Update</button>
    </div>`;
}

async function updateCourse(id) {
  const title = document.getElementById('ec-title').value.trim();
  const description = document.getElementById('ec-desc').value.trim();
  const res = await apiFetch('/courses/' + id + '/', {
    method: 'PATCH',
    body: JSON.stringify({ title, description })
  });
  const data = await res.json();
  if (res.ok) {
    showSuccess('edit-course-success', 'Updated!');
    loadMyCourses();
  } else {
    showError('edit-course-error', JSON.stringify(data));
  }
}

async function enroll(courseId) {
  const res = await apiFetch('/courses/enrollments/', {
    method: 'POST',
    body: JSON.stringify({ course: courseId })
  });
  const data = await res.json();
  if (res.ok) {
    alert('Enrolled in course #' + courseId + '!');
  } else {
    alert(JSON.stringify(data));
  }
}

// ============================================================
// Enrollments (student)
// ============================================================
async function loadEnrollments() {
  setActive('nav-enrollments');
  setContent('<h3>My Enrollments</h3><p class="section-msg">Loading...</p>');
  const res = await apiFetch('/courses/enrollments/');
  const data = await res.json();

  let rows = data.map(e => `
    <tr>
      <td>${e.id}</td>
      <td>${e.course}</td>
      <td>${e.enrolled_at ? e.enrolled_at.substring(0,10) : ''}</td>
      <td><button class="btn-danger" onclick="unenroll(${e.id})">Unenroll</button></td>
    </tr>`).join('');

  setContent(`
    <h3>My Enrollments</h3>
    <table>
      <thead><tr><th>ID</th><th>Course ID</th><th>Enrolled At</th><th>Action</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="4" class="section-msg">Not enrolled in any course.</td></tr>'}</tbody>
    </table>`);
}

async function unenroll(enrollmentId) {
  if (!confirm('Unenroll?')) return;
  const res = await apiFetch('/courses/enrollments/' + enrollmentId + '/', { method: 'DELETE' });
  if (res.ok || res.status === 204) {
    loadEnrollments();
  } else {
    const data = await res.json();
    alert(JSON.stringify(data));
  }
}

// ============================================================
// Topics
// ============================================================
async function loadTopics() {
  setActive('nav-topics');
  setContent('<h3>Topics</h3><p class="section-msg">Loading...</p>');
  const res = await apiFetch('/courses/topics/');
  const data = await res.json();
  const isMentor = currentUser.role === 'mentor';

  let rows = data.map(t => `
    <tr>
      <td>${t.id}</td>
      <td>${t.course}</td>
      <td>${t.title}</td>
      <td class="status-${t.upload_status}">${t.upload_status}</td>
      ${isMentor ? `<td><button class="btn-danger" onclick="deleteTopic(${t.id})">Delete</button></td>` : ''}
    </tr>`).join('');

  let createForm = isMentor ? `
    <div class="form-box" style="margin-top:20px">
      <h4>Add New Topic</h4>
      <div id="topic-error" class="error-msg"></div>
      <div id="topic-success" class="success-msg"></div>
      <label>Course ID</label>
      <input type="number" id="t-course" placeholder="Course ID" />
      <label>Title</label>
      <input type="text" id="t-title" placeholder="Topic title" />
      <label>Material (file)</label>
      <input type="file" id="t-material" />
      <label>Thumbnail (image)</label>
      <input type="file" id="t-thumb" />
      <button onclick="createTopic()">Add Topic</button>
    </div>` : '';

  setContent(`
    <h3>Topics</h3>
    <table>
      <thead><tr><th>ID</th><th>Course</th><th>Title</th><th>Status</th>${isMentor ? '<th>Action</th>' : ''}</tr></thead>
      <tbody>${rows || '<tr><td colspan="5" class="section-msg">No topics found.</td></tr>'}</tbody>
    </table>
    ${createForm}`);
}

async function createTopic() {
  hideError('topic-error');
  const courseId = document.getElementById('t-course').value;
  const title = document.getElementById('t-title').value.trim();
  const materialFile = document.getElementById('t-material').files[0];
  const thumbFile = document.getElementById('t-thumb').files[0];

  if (!courseId || !title || !materialFile || !thumbFile) {
    return showError('topic-error', 'Please fill in all fields including files.');
  }

  const fd = new FormData();
  fd.append('course', courseId);
  fd.append('title', title);
  fd.append('material', materialFile);
  fd.append('thumbnail', thumbFile);

  const res = await apiFetch('/courses/topics/', { method: 'POST', body: fd });
  const data = await res.json();
  if (res.ok) {
    showSuccess('topic-success', 'Topic created! ID: ' + data.id);
    loadTopics();
  } else {
    showError('topic-error', JSON.stringify(data));
  }
}

async function deleteTopic(id) {
  if (!confirm('Delete topic #' + id + '?')) return;
  const res = await apiFetch('/courses/topics/' + id + '/', { method: 'DELETE' });
  if (res.ok || res.status === 204) { loadTopics(); }
  else { const d = await res.json(); alert(JSON.stringify(d)); }
}

// ============================================================
// Assignments
// ============================================================
async function loadAssignments() {
  setActive('nav-assignments');
  setContent('<h3>Assignments</h3><p class="section-msg">Loading...</p>');
  const res = await apiFetch('/courses/assignments/');
  const data = await res.json();
  const isMentor = currentUser.role === 'mentor';

  let rows = data.map(a => `
    <tr>
      <td>${a.id}</td>
      <td>${a.topic}</td>
      <td>${a.title}</td>
      <td>${a.description}</td>
      <td>${a.created_at ? a.created_at.substring(0,10) : ''}</td>
      ${isMentor ? `<td><button class="btn-danger" onclick="deleteAssignment(${a.id})">Delete</button></td>` : ''}
    </tr>`).join('');

  let createForm = isMentor ? `
    <div class="form-box" style="margin-top:20px">
      <h4>Add Assignment</h4>
      <div id="asgn-error" class="error-msg"></div>
      <div id="asgn-success" class="success-msg"></div>
      <label>Topic ID</label>
      <input type="number" id="a-topic" placeholder="Topic ID" />
      <label>Title</label>
      <input type="text" id="a-title" placeholder="Assignment title" />
      <label>Description</label>
      <textarea id="a-desc" placeholder="Assignment description"></textarea>
      <button onclick="createAssignment()">Add Assignment</button>
    </div>` : '';

  setContent(`
    <h3>Assignments</h3>
    <table>
      <thead><tr><th>ID</th><th>Topic</th><th>Title</th><th>Description</th><th>Created</th>${isMentor ? '<th>Action</th>' : ''}</tr></thead>
      <tbody>${rows || '<tr><td colspan="6" class="section-msg">No assignments.</td></tr>'}</tbody>
    </table>
    ${createForm}`);
}

async function createAssignment() {
  hideError('asgn-error');
  const topic = document.getElementById('a-topic').value;
  const title = document.getElementById('a-title').value.trim();
  const description = document.getElementById('a-desc').value.trim();
  if (!topic || !title || !description) return showError('asgn-error', 'All fields required.');

  const res = await apiFetch('/courses/assignments/', {
    method: 'POST',
    body: JSON.stringify({ topic: parseInt(topic), title, description })
  });
  const data = await res.json();
  if (res.ok) {
    showSuccess('asgn-success', 'Assignment created!');
    loadAssignments();
  } else {
    showError('asgn-error', JSON.stringify(data));
  }
}

async function deleteAssignment(id) {
  if (!confirm('Delete assignment #' + id + '?')) return;
  const res = await apiFetch('/courses/assignments/' + id + '/', { method: 'DELETE' });
  if (res.ok || res.status === 204) { loadAssignments(); }
  else { const d = await res.json(); alert(JSON.stringify(d)); }
}

// ============================================================
// Submissions
// ============================================================
async function loadSubmissions() {
  setActive('nav-submissions');
  setContent('<h3>Submissions</h3><p class="section-msg">Loading...</p>');
  const res = await apiFetch('/courses/submissions/');
  const data = await res.json();
  const isMentor = currentUser.role === 'mentor';

  let rows = data.map(s => `
    <tr>
      <td>${s.id}</td>
      <td>${s.assignment}</td>
      <td>${isMentor ? (s.student_username || s.student) : ''}</td>
      <td><a href="${API}${s.file}" target="_blank">View File</a></td>
      <td class="grade-badge">${s.marks !== null ? s.marks : '-'}</td>
      <td>${s.submitted_at ? s.submitted_at.substring(0,10) : ''}</td>
      ${isMentor ? `<td>
        <input type="number" id="marks-${s.id}" placeholder="Marks" style="width:70px;padding:3px;" value="${s.marks || ''}"/>
        <button class="btn-action" style="margin-left:4px" onclick="gradeSubmission(${s.id})">Grade</button>
      </td>` : ''}
    </tr>`).join('');

  const cols = isMentor
    ? '<th>ID</th><th>Assignment</th><th>Student</th><th>File</th><th>Marks</th><th>Submitted</th><th>Grade</th>'
    : '<th>ID</th><th>Assignment</th><th></th><th>File</th><th>Marks</th><th>Submitted</th>';

  setContent(`
    <h3>Submissions</h3>
    <table>
      <thead><tr>${cols}</tr></thead>
      <tbody>${rows || '<tr><td colspan="7" class="section-msg">No submissions.</td></tr>'}</tbody>
    </table>`);
}

async function gradeSubmission(id) {
  const marks = document.getElementById('marks-' + id).value;
  if (marks === '') return alert('Enter marks first.');
  const res = await apiFetch('/courses/submissions/' + id + '/grade/', {
    method: 'PATCH',
    body: JSON.stringify({ marks: parseInt(marks) })
  });
  const data = await res.json();
  if (res.ok) {
    alert('Graded successfully!');
    loadSubmissions();
  } else {
    alert(JSON.stringify(data));
  }
}

// ============================================================
// Submit Assignment (student)
// ============================================================
async function loadSubmitForm() {
  setActive('nav-submit');
  setContent(`
    <h3>Submit Assignment</h3>
    <div class="form-box">
      <div id="sub-error" class="error-msg"></div>
      <div id="sub-success" class="success-msg"></div>
      <label>Assignment ID</label>
      <input type="number" id="sub-assignment" placeholder="Assignment ID" />
      <label>File</label>
      <input type="file" id="sub-file" />
      <button onclick="submitAssignment()">Submit</button>
    </div>`);
}

async function submitAssignment() {
  hideError('sub-error');
  const assignmentId = document.getElementById('sub-assignment').value;
  const file = document.getElementById('sub-file').files[0];
  if (!assignmentId || !file) return showError('sub-error', 'Please fill all fields.');

  const fd = new FormData();
  fd.append('assignment', assignmentId);
  fd.append('file', file);

  const res = await apiFetch('/courses/submissions/', { method: 'POST', body: fd });
  const data = await res.json();
  if (res.ok) {
    showSuccess('sub-success', 'Submitted successfully! ID: ' + data.id);
  } else {
    showError('sub-error', JSON.stringify(data));
  }
}

// ============================================================
// Utility
// ============================================================
function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ============================================================
// Init
// ============================================================
(function init() {
  if (accessToken && currentUser) {
    loadApp();
  } else {
    showPage('page-login');
  }
})();
