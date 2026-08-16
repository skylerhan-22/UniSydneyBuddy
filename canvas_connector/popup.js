const statusNode = document.getElementById("status");
const formNode = document.getElementById("course-form");
const coursesNode = document.getElementById("courses");
const syncButton = document.getElementById("sync");
const endpointNode = document.getElementById("endpoint");
let canvasTabId = null;

function setStatus(message, type = "info") {
  statusNode.textContent = message;
  statusNode.style.borderLeftColor = type === "error" ? "#a31f1f" : type === "success" ? "#2d7a4b" : "#e64626";
}

async function canvasTab() {
  const tabs = await chrome.tabs.query({ url: "https://canvas.sydney.edu.au/*" });
  return tabs[0] || null;
}

async function sendCanvas(message) {
  if (!canvasTabId) throw new Error("没有找到已登录的悉大 Canvas 页面");
  return chrome.tabs.sendMessage(canvasTabId, message);
}

function renderCourses(courses) {
  coursesNode.replaceChildren();
  for (const course of courses) {
    const label = document.createElement("label");
    label.className = "course";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = "course";
    checkbox.value = String(course.id);
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = course.course_code ? `${course.course_code} · ${course.name}` : course.name;
    const meta = document.createElement("span");
    meta.textContent = course.term || "Canvas course";
    copy.append(title, meta);
    label.append(checkbox, copy);
    coursesNode.append(label);
  }
}

async function initialise() {
  try {
    const saved = await chrome.storage.local.get(["syncEndpoint"]);
    endpointNode.value = saved.syncEndpoint || "http://127.0.0.1:8765/canvas-sync";
    const tab = await canvasTab();
    if (!tab) throw new Error("请先打开并登录 canvas.sydney.edu.au，然后重新打开插件");
    canvasTabId = tab.id;
    const result = await sendCanvas({ type: "DISCOVER_COURSES" });
    if (!result?.ok) throw new Error(result?.error || "无法读取课程");
    renderCourses(result.courses);
    formNode.hidden = false;
    setStatus(`已连接 Canvas，找到 ${result.courses.length} 门当前课程`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

formNode.addEventListener("submit", async (event) => {
  event.preventDefault();
  const courseIds = [...document.querySelectorAll('input[name="course"]:checked')].map((item) => Number(item.value));
  if (!courseIds.length) {
    setStatus("请至少选择一门课程", "error");
    return;
  }
  syncButton.disabled = true;
  setStatus("正在读取 Modules、Assignments、Pages 和 Announcements…");
  try {
    const result = await sendCanvas({ type: "SYNC_COURSES", courseIds });
    if (!result?.ok) throw new Error(result?.error || "Canvas 同步失败");
    const syncEndpoint = endpointNode.value.trim();
    await chrome.storage.local.set({ syncEndpoint });
    const response = await fetch(syncEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result.snapshot)
    });
    const body = await response.json();
    if (!response.ok || !body.ok) throw new Error(body.error || "本地 UniSydneyBuddy 未接收数据");
    await chrome.storage.local.set({ lastSync: result.snapshot.synced_at, courseCount: result.snapshot.courses.length });
    setStatus(`同步完成：${result.snapshot.courses.length} 门课程。返回网站并刷新页面。`, "success");
  } catch (error) {
    setStatus(`${error.message}。请确认同步地址正确且 UniSydneyBuddy 服务正在运行。`, "error");
  } finally {
    syncButton.disabled = false;
  }
});

initialise();
