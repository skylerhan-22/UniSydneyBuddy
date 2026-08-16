const CANVAS_BASE = "https://canvas.sydney.edu.au";

function nextLink(header) {
  if (!header) return null;
  for (const part of header.split(",")) {
    const match = part.match(/<([^>]+)>;\s*rel="([^"]+)"/);
    if (match && match[2] === "next") return match[1];
  }
  return null;
}

async function canvasFetch(url) {
  const response = await fetch(url, {
    credentials: "include",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw new Error(`Canvas request failed (${response.status})`);
  }
  return response;
}

async function fetchAll(path) {
  let url = path.startsWith("http") ? path : `${CANVAS_BASE}${path}`;
  const rows = [];
  while (url) {
    const response = await canvasFetch(url);
    const page = await response.json();
    if (!Array.isArray(page)) throw new Error("Canvas returned an unexpected list response");
    rows.push(...page);
    url = nextLink(response.headers.get("Link"));
  }
  return rows;
}

async function fetchOne(path) {
  const response = await canvasFetch(path.startsWith("http") ? path : `${CANVAS_BASE}${path}`);
  return response.json();
}

async function discoverCourses() {
  const courses = await fetchAll(
    "/api/v1/courses?enrollment_state=active&state[]=available&include[]=term&per_page=100"
  );
  return courses
    .filter((course) => course.id && (course.name || course.course_code))
    .map((course) => ({
      id: course.id,
      name: course.name || course.course_code,
      course_code: course.course_code || "",
      term: course.term?.name || ""
    }));
}

async function moduleWithItems(courseId, module) {
  let items = Array.isArray(module.items) ? module.items : [];
  if (!items.length && module.items_count) {
    items = await fetchAll(
      `/api/v1/courses/${courseId}/modules/${module.id}/items?include[]=content_details&per_page=100`
    );
  }
  const enrichedItems = [];
  for (const item of items) {
    const output = {
      id: item.id,
      title: item.title,
      type: item.type,
      html_url: item.html_url || null,
      content_id: item.content_id || null,
      page_url: item.page_url || null,
      content_details: item.content_details || null
    };
    if (item.type === "Page" && item.page_url) {
      try {
        const page = await fetchOne(
          `/api/v1/courses/${courseId}/pages/${encodeURIComponent(item.page_url)}`
        );
        output.page = {
          title: page.title,
          body: page.body || "",
          updated_at: page.updated_at || null,
          url: page.url || item.page_url
        };
      } catch (_error) {
        output.page = null;
      }
    }
    enrichedItems.push(output);
  }
  return {
    id: module.id,
    name: module.name,
    position: module.position,
    unlock_at: module.unlock_at || null,
    state: module.state || null,
    items: enrichedItems
  };
}

async function syncCourse(courseId) {
  const course = await fetchOne(
    `/api/v1/courses/${courseId}?include[]=syllabus_body&include[]=term`
  );
  const modulesRaw = await fetchAll(
    `/api/v1/courses/${courseId}/modules?include[]=items&include[]=content_details&per_page=100`
  );
  const modules = [];
  for (const module of modulesRaw) modules.push(await moduleWithItems(courseId, module));
  const assignments = await fetchAll(
    `/api/v1/courses/${courseId}/assignments?include[]=rubric&per_page=100`
  );
  const announcements = await fetchAll(
    `/api/v1/announcements?context_codes[]=course_${courseId}&active_only=true&per_page=100`
  );
  return {
    id: course.id,
    name: course.name || course.course_code,
    course_code: course.course_code || "",
    term: course.term?.name || "",
    syllabus_body: course.syllabus_body || "",
    modules,
    assignments: assignments.map((assignment) => ({
      id: assignment.id,
      name: assignment.name,
      description: assignment.description || "",
      due_at: assignment.due_at || null,
      unlock_at: assignment.unlock_at || null,
      lock_at: assignment.lock_at || null,
      points_possible: assignment.points_possible,
      submission_types: assignment.submission_types || [],
      html_url: assignment.html_url || null,
      rubric: assignment.rubric || []
    })),
    announcements: announcements.map((announcement) => ({
      id: announcement.id,
      title: announcement.title,
      message: announcement.message || "",
      posted_at: announcement.posted_at || null,
      updated_at: announcement.updated_at || null,
      html_url: announcement.html_url || null
    }))
  };
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "DISCOVER_COURSES") {
    discoverCourses()
      .then((courses) => sendResponse({ ok: true, courses }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }
  if (message?.type === "SYNC_COURSES") {
    Promise.all(message.courseIds.map((courseId) => syncCourse(courseId)))
      .then((courses) =>
        sendResponse({
          ok: true,
          snapshot: {
            schema_version: 1,
            source: "unisydneybuddy_canvas_connector",
            canvas_base: CANVAS_BASE,
            synced_at: new Date().toISOString(),
            courses
          }
        })
      )
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }
  return false;
});
