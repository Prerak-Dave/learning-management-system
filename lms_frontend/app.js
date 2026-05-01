// ─────────────────────────────────────────────
// CONFIG — change BASE_URL if your server runs
// on a different host or port
// ─────────────────────────────────────────────
const BASE_URL = 'http://127.0.0.1:8000';

let isRefreshing = false;
let refreshPromise = null;

// In-memory token store (cleared on page refresh)
const S = { access: null, refresh: null };

// ─────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────

function val(id) {
  return document.getElementById(id).value.trim();
}

function numVal(id) {
  return parseInt(document.getElementById(id).value) || null;
}

// Display API response below a form
function show(id, data, ok) {
  const el = document.getElementById(id);
  el.className = 'response show ' + (ok ? 'ok' : 'err');
  el.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
}

// Generic authenticated API call
async function api(method, path, body, isForm, retry=true) {
  const headers = { Authorization: 'Bearer ' + S.access };
  if (!isForm) headers['Content-Type'] = 'application/json';

  const opts = { method, headers };
  if (body) opts.body = isForm ? body : JSON.stringify(body);

  const r = await fetch(BASE_URL + path, opts);

  if(r.status === 401 && retry){
    if(!isRefreshing){
      isRefreshing = true;
      refreshPromise = refreshToken().finally(() => {
        isRefreshing = false;
      })
    }

    const success = await refreshPromise;

    if(!success){
      logout();
      return{ok: false, status: 401, data: "Session expired"}
    }

    return api(method, path, body, isForm, false);
  }

  let data;

  try {
    data = await r.json();
  } catch {
    data = r.status === 204 ? 'Deleted successfully' : await r.text();
  }
  return { ok: r.ok, status: r.status, data };
}

// ─────────────────────────────────────────────
// NAVIGATION
// ─────────────────────────────────────────────

function go(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => {
    if (n.getAttribute('onclick') === "go('" + name + "')") {
      n.classList.add('active');
    }
  });
  if (name === 'enrollments') listEnrollments();
}

function authTab(tab) {
  document.getElementById('tab-login').classList.toggle('hidden', tab !== 'login');
  document.getElementById('tab-signup').classList.toggle('hidden', tab !== 'signup');
  document.querySelectorAll('.auth-tab').forEach((t, i) => {
    t.classList.toggle('active', (tab === 'login') === (i === 0));
  });
}

function setLoggedIn(username, isMentor) {
  document.getElementById('sidebar').classList.remove('hidden');
  document.getElementById('hdr-user').classList.remove('hidden');
  document.getElementById('hdr-user').textContent =
    username + ' (' + (isMentor ? 'Mentor' : 'Student') + ')';
  document.getElementById('btn-logout').classList.remove('hidden');
  document.getElementById('nav-mentor').style.display = isMentor ? 'block' : 'none';
  document.getElementById('nav-student').style.display = isMentor ? 'none' : 'block';
  go('courses');
  listCourses();
}

function logout() {
  // Blacklist the refresh token on the server
  if (S.refresh) {
    fetch(BASE_URL + '/auth/logout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + S.access
      },
      body: JSON.stringify({ refresh: S.refresh })
    }).catch(() => {});
  }

  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  S.access = null;
  S.refresh = null;

  document.getElementById('sidebar').classList.add('hidden');
  document.getElementById('hdr-user').classList.add('hidden');
  document.getElementById('btn-logout').classList.add('hidden');
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-auth').classList.add('active');
}

// ─────────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────────

async function login() {
  const username = val('l-username');
  const password = val('l-password');
  const roleEl = document.querySelector('input[name="login-role"]:checked');

  if (!username || !password || !roleEl) {
    show('r-login', 'Fill all fields and select a role', false);
    return;
  }

  const role = parseInt(roleEl.value);

  try {
    const r = await fetch(BASE_URL + '/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, role })
    });
    const data = await r.json();

    if (r.ok && data.access) {
      S.access = data.access;
      S.refresh = data.refresh;
      setLoggedIn(username, role === 1);
    } else {
      show('r-login', data, false);
    }
  } catch (e) {
    show('r-login', e.message, false);
  }
}

async function signup() {
  const username = val('s-username');
  const email = val('s-email');
  const password = val('s-password');
  const password2 = val('s-password2');
  const role = [...document.querySelectorAll('.signup-role:checked')]
    .map(c => parseInt(c.value));

  if (!username || !email || !password || !role.length) {
    show('r-signup', 'Fill all fields and select at least one role', false);
    return;
  }

  try {
    const r = await fetch(BASE_URL + '/auth/signup/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, password2, role })
    });
    const data = await r.json();
    show('r-signup', data, r.ok);
    if (r.ok) setTimeout(() => authTab('login'), 800);
  } catch (e) {
    show('r-signup', e.message, false);
  }
}

async function refreshToken() {
  if(!S.refresh) return false;

  try {
    const r = await fetch(BASE_URL + '/auth/login/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh : S.refresh })
    });
    if(!r.ok) return false;

    const data = await r.json();
    if (data.access) S.access = data.access;
    localStorage.setItem("access", data.access);
    return true;
  } catch {
    return false;
  }
}

// ─────────────────────────────────────────────
// COURSES
// ─────────────────────────────────────────────

async function listCourses() {
  let url = '/courses/?';
  const s = val('c-search');
  const cr = val('c-creator');
  if (s) url += 'search=' + encodeURIComponent(s) + '&';
  if (cr) url += 'creator=' + cr + '&';
  url = url.replace(/[?&]$/, '');

  const r = await api('GET', url);

  if (!r.ok) {
    document.getElementById('courses-list').innerHTML =
      '<div class="empty" style="color:#dc2626">' + JSON.stringify(r.data) + '</div>';
    return;
  }

  const list = Array.isArray(r.data) ? r.data : (r.data.results || []);

  if (!list.length) {
    document.getElementById('courses-list').innerHTML = '<div class="empty">No courses found</div>';
    return;
  }

  const isMentor = document.getElementById('nav-mentor').style.display !== 'none';
  const enrollCol = isMentor ? '' : '<th></th>';

  document.getElementById('courses-list').innerHTML =
    '<table><thead><tr><th>ID</th><th>Title</th><th>Description</th><th>Start Date</th>' + enrollCol + '</tr></thead><tbody>' +
    list.map(c => {
      const enrollBtn = isMentor ? '' :
        '<td><button class="btn btn-primary" style="padding:4px 10px;font-size:12px" onclick="enrollFromList(' + c.id + ')">Enroll</button></td>';
      return '<tr><td>' + c.id + '</td><td>' + c.title + '</td><td>' +
        (c.description || '') + '</td><td>' + (c.start_date || '') + '</td>' + enrollBtn + '</tr>';
    }).join('') +
    '</tbody></table>';
}

async function enrollFromList(courseId) {
  const r = await api('POST', '/courses/enrollments/', { course: courseId });
  show('r-course-enroll', r.ok ? 'Enrolled in course #' + courseId : r.data, r.ok);
  if (r.ok) listCourses();
}

async function getCourse() {
  const id = val('gc-id');
  if (!id) { show('r-get-course', 'Enter a course ID', false); return; }
  const r = await api('GET', '/courses/' + id + '/');
  show('r-get-course', r.data, r.ok);
}

async function createCourse() {
  const title = val('cc-title');
  const description = val('cc-desc');
  if (!title || !description) { show('r-create-course', 'Fill title and description', false); return; }
  const r = await api('POST', '/courses/', { title, description });
  show('r-create-course', r.data, r.ok);
}

async function updateCourse(method) {
  const id = val('uc-id');
  if (!id) { show('r-update-course', 'Enter course ID', false); return; }
  const body = {};
  const t = val('uc-title');
  const d = val('uc-desc');
  if (t) body.title = t;
  if (d) body.description = d;
  const r = await api(method, '/courses/' + id + '/', body);
  show('r-update-course', r.data, r.ok);
}

async function deleteCourse() {
  const id = val('dc-id');
  if (!id) { show('r-delete-course', 'Enter course ID', false); return; }
  const r = await api('DELETE', '/courses/' + id + '/');
  show('r-delete-course', r.data, r.ok || r.status === 204);
}

// ─────────────────────────────────────────────
// ENROLLMENTS
// ─────────────────────────────────────────────

async function listEnrollments() {
  const r = await api('GET', '/courses/enrollments/');
  const el = document.getElementById('enrollments-list');

  if (!r.ok) {
    el.innerHTML = '<div class="empty" style="color:#dc2626">' + JSON.stringify(r.data) + '</div>';
    return;
  }

  const list = Array.isArray(r.data) ? r.data : (r.data.results || []);

  if (!list.length) {
    el.innerHTML = '<div class="empty">You are not enrolled in any courses yet</div>';
    return;
  }

  el.innerHTML =
    '<table><thead><tr><th>Enrollment ID</th><th>Course ID</th><th>Course Title</th><th></th></tr></thead><tbody>' +
    list.map(e =>
      '<tr><td>' + e.id + '</td><td>' + (e.course || e.course_id || '') + '</td><td>' +
      (e.course_title || e.title || '') + '</td><td>' +
      '<button class="btn btn-danger" style="padding:4px 10px;font-size:12px" onclick="unenrollFromList(' + e.id + ')">Unenroll</button></td></tr>'
    ).join('') +
    '</tbody></table>';
}

async function enroll() {
  const course = numVal('enroll-id');
  if (!course) { show('r-enroll', 'Enter course ID', false); return; }
  const r = await api('POST', '/courses/enrollments/', { course });
  show('r-enroll', r.ok ? 'Enrolled successfully' : r.data, r.ok);
  if (r.ok) { document.getElementById('enroll-id').value = ''; listEnrollments(); }
}

async function unenrollFromList(id) {
  const r = await api('DELETE', '/courses/enrollments/' + id + '/');
  show('r-unenroll', r.ok || r.status === 204 ? 'Unenrolled successfully' : r.data, r.ok || r.status === 204);
  if (r.ok || r.status === 204) listEnrollments();
}

async function unenroll() {
  const id = val('unenroll-id');
  if (!id) { show('r-unenroll', 'Enter enrollment ID', false); return; }
  const r = await api('DELETE', '/courses/enrollments/' + id + '/');
  show('r-unenroll', r.ok || r.status === 204 ? 'Unenrolled successfully' : r.data, r.ok || r.status === 204);
  if (r.ok || r.status === 204) listEnrollments();
}

// ─────────────────────────────────────────────
// TOPICS
// ─────────────────────────────────────────────

async function listTopics(resId, inputId) {
  const course = val(inputId);
  const r = await api('GET', '/courses/topics/' + (course ? '?course=' + course : ''));
  show(resId, r.data, r.ok);
}

async function createTopic() {
  const course = val('ct-course');
  const title = val('ct-title');
  if (!course || !title) { show('r-create-topic', 'Fill course ID and title', false); return; }

  const fd = new FormData();
  fd.append('course', course);
  fd.append('title', title);
  const mat = document.getElementById('ct-material').files[0];
  const thumb = document.getElementById('ct-thumb').files[0];
  if (mat) fd.append('material', mat);
  if (thumb) fd.append('thumbnail', thumb);

  const r = await api('POST', '/courses/topics/', fd, true);
  show('r-create-topic', r.data, r.ok);
}

async function updateTopic() {
  const id = val('ut-id');
  const title = val('ut-title');
  if (!id) { show('r-update-topic', 'Enter topic ID', false); return; }
  const r = await api('PATCH', '/courses/topics/' + id + '/', { title });
  show('r-update-topic', r.data, r.ok);
}

async function deleteTopic() {
  const id = val('dt-id');
  if (!id) { show('r-delete-topic', 'Enter topic ID', false); return; }
  const r = await api('DELETE', '/courses/topics/' + id + '/');
  show('r-delete-topic', r.data, r.ok || r.status === 204);
}

// ─────────────────────────────────────────────
// ASSIGNMENTS
// ─────────────────────────────────────────────

async function listAssignments(resId, inputId) {
  const topic = val(inputId);
  const r = await api('GET', '/courses/assignments/' + (topic ? '?topic=' + topic : ''));
  show(resId, r.data, r.ok);
}

async function createAssignment() {
  const topic = numVal('ca-topic');
  const title = val('ca-title');
  const description = val('ca-desc');
  if (!topic || !title || !description) { show('r-create-assign', 'Fill all fields', false); return; }
  const r = await api('POST', '/courses/assignments/', { topic, title, description });
  show('r-create-assign', r.data, r.ok);
}

async function updateAssignment() {
  const id = val('ua-id');
  if (!id) { show('r-update-assign', 'Enter assignment ID', false); return; }
  const body = {};
  const t = val('ua-title');
  const d = val('ua-desc');
  if (t) body.title = t;
  if (d) body.description = d;
  const r = await api('PATCH', '/courses/assignments/' + id + '/', body);
  show('r-update-assign', r.data, r.ok);
}

async function deleteAssignment() {
  const id = val('da-id');
  if (!id) { show('r-delete-assign', 'Enter assignment ID', false); return; }
  const r = await api('DELETE', '/courses/assignments/' + id + '/');
  show('r-delete-assign', r.data, r.ok || r.status === 204);
}

// ─────────────────────────────────────────────
// SUBMISSIONS
// ─────────────────────────────────────────────

async function listSubmissions() {
  let url = '/courses/submissions/?';
  const a = val('fs-assign');
  const s = val('fs-student');
  if (a) url += 'assignment=' + a + '&';
  if (s) url += 'student=' + s + '&';
  const r = await api('GET', url.replace(/[?&]$/, ''));
  show('r-list-sub', r.data, r.ok);
}

async function gradeSubmission() {
  const id = val('gs-id');
  const marks = numVal('gs-marks');
  if (!id || marks === null) { show('r-grade', 'Enter submission ID and marks', false); return; }
  const r = await api('PATCH', '/courses/submissions/' + id + '/grade/', { marks });
  show('r-grade', r.data, r.ok);
}

async function mySubmissions() {
  const r = await api('GET', '/courses/submissions/');
  show('r-my-sub', r.data, r.ok);
}

async function submitAssignment() {
  const assignment = val('sub-assign-id');
  const file = document.getElementById('sub-file').files[0];
  if (!assignment || !file) { show('r-submit', 'Select assignment ID and a file', false); return; }

  const fd = new FormData();
  fd.append('assignment', assignment);
  fd.append('file', file);

  const r = await api('POST', '/courses/submissions/', fd, true);
  show('r-submit', r.data, r.ok);
}

// ─────────────────────────────────────────────
// ENROLLED STUDENTS (mentor)
// ─────────────────────────────────────────────

async function enrolledStudents() {
  const id = val('es-course');
  if (!id) { show('r-enrolled-students', 'Enter course ID', false); return; }
  const r = await api('GET', '/courses/' + id + '/enrolled-students/');
  show('r-enrolled-students', r.data, r.ok);
}
