const byId = (id) => document.getElementById(id);
const list = byId("records");
const query = byId("search");
const topic = byId("topic");
const detail = byId("source-detail");
const empty = byId("empty");
let selectedId;
let request;
let pending;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function showDetail(record) {
  const items = element("dl");
  const fields = [
    ["Publisher", record.publisher],
    ["Source type", record.source_type],
    ["Document ID", record.source_ref],
    ["Source key", record.source_id],
    ["Published", record.published],
    ["Setting", record.setting],
  ];
  for (const [label, value] of fields) {
    const row = element("div");
    row.append(element("dt", label), element("dd", value ?? "Not recorded"));
    items.append(row);
  }
  detail.replaceChildren(element("h3", record.title), element("p", record.observation), items);
}

function render({ records, topics, summary }) {
  byId("count").textContent = summary.records;
  byId("sources").textContent = summary.sources;
  byId("duplicates").textContent = summary.duplicates;
  byId("result-count").textContent = `${records.length} of ${summary.records} records`;
  if (topic.options.length === 1) {
    for (const name of topics) {
      const label = name[0].toUpperCase() + name.slice(1);
      topic.add(new Option(label, name));
    }
  }
  const selected = records.find((record) => record.record_id === selectedId) ?? records[0];
  selectedId = selected?.record_id;
  if (selected) showDetail(selected);
  else detail.replaceChildren(element("p", "No source selected.", "placeholder"));

  list.replaceChildren(...records.map((record) => {
    const row = element("li");
    const button = element("button", "", "record");
    const heading = element("span", "", "record-head");
    heading.append(element("strong", record.title), element("span", record.status, "status"));
    button.type = "button";
    button.setAttribute("aria-controls", "source-detail");
    button.setAttribute("aria-pressed", String(record.record_id === selectedId));
    button.append(heading, element("small", record.publisher ?? "Source unavailable"));
    button.addEventListener("click", () => {
      selectedId = record.record_id;
      list.querySelector('[aria-pressed="true"]')?.setAttribute("aria-pressed", "false");
      button.setAttribute("aria-pressed", "true");
      showDetail(record);
      if (matchMedia("(max-width: 690px)").matches) byId("detail-title").focus();
    });
    row.append(button);
    return row;
  }));
  empty.hidden = records.length > 0;
  empty.textContent = "No observations match these filters.";
}

async function load() {
  request?.abort();
  request = new AbortController();
  const params = new URLSearchParams({ q: query.value, topic: topic.value });
  try {
    const response = await fetch(`/api/evidence?${params}`, { signal: request.signal });
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    render(await response.json());
  } catch (error) {
    if (error.name === "AbortError") return;
    byId("result-count").textContent = "Results unavailable";
    list.replaceChildren();
    detail.replaceChildren(element("p", "No source selected.", "placeholder"));
    empty.textContent = "Could not load records. Check the local server and try again.";
    empty.hidden = false;
  }
}

query.addEventListener("input", () => {
  clearTimeout(pending);
  pending = setTimeout(load, 150);
});
topic.addEventListener("change", () => {
  clearTimeout(pending);
  load();
});
load();
