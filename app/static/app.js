const state = {
  assets: [],
  selected: null,
  cart: [],
  plans: [],
};

const $ = (selector) => document.querySelector(selector);
const money = (cents) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(cents / 100);

const filters = {
  q: $("#searchInput"),
  category: $("#categorySelect"),
  format: $("#formatSelect"),
  engine: $("#engineSelect"),
  sort: $("#sortSelect"),
  curated: $("#curatedOnly"),
};

async function api(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(path, {
    headers: isFormData ? { ...(options.headers || {}) } : { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(Array.isArray(error.detail) ? error.detail[0].msg : error.detail);
  }
  return response.json();
}

function queryString() {
  const params = new URLSearchParams();
  if (filters.q.value.trim()) params.set("q", filters.q.value.trim());
  if (filters.category.value) params.set("category", filters.category.value);
  if (filters.format.value) params.set("format", filters.format.value);
  if (filters.engine.value) params.set("engine", filters.engine.value);
  if (filters.curated.checked) params.set("curated", "true");
  params.set("sort", filters.sort.value);
  return params.toString();
}

async function fetchSearchResults(query) {
  if (!query.trim()) {
    await loadAssets();
    return;
  }

  try {
    const results = await api(`/api/search?q=${encodeURIComponent(query.trim())}`);
    state.assets = results;
    $("#assetCount").textContent = state.assets.length;
    renderAssets();
    if (!state.selected && state.assets.length) {
      selectAsset(state.assets[0].slug);
    } else if (state.selected) {
      const exists = state.assets.find((asset) => asset.slug === state.selected.slug);
      if (!exists && state.assets.length) selectAsset(state.assets[0].slug);
    }
  } catch (error) {
    $("#assetGrid").innerHTML = `<div class="empty-grid">${error.message}</div>`;
    $("#detailPanel").innerHTML = `
      <div class="empty-state">
        <span class="empty-mark">FX</span>
        <h2>No search results</h2>
        <p>${error.message}</p>
      </div>
    `;
  }
}

async function loadAssets() {
  const qs = queryString();
  state.assets = await api(`/api/assets${qs ? `?${qs}` : ""}`);
  $("#assetCount").textContent = state.assets.length;
  renderAssets();
  if (!state.selected && state.assets.length) {
    selectAsset(state.assets[0].slug);
  } else if (state.selected) {
    const exists = state.assets.find((asset) => asset.slug === state.selected.slug);
    if (!exists && state.assets.length) selectAsset(state.assets[0].slug);
  }
}

function renderAssets() {
  const grid = $("#assetGrid");
  if (!state.assets.length) {
    grid.innerHTML = '<div class="empty-grid">No matching assets</div>';
    return;
  }

  const previewMarkup = (asset) => {
    if (/\.(mov|mp4)(?:$|[?#])/i.test(asset.preview_url)) {
      return `<video src="${asset.preview_url}" muted loop playsinline preload="metadata"></video>`;
    }
    return `<img src="${asset.preview_url}" alt="${asset.title} preview">`;
  };

  grid.innerHTML = state.assets
    .map(
      (asset) => `
      <article class="asset-card">
        <button type="button" data-select="${asset.slug}">
          <div class="thumb">
            ${previewMarkup(asset)}
            <div class="badge-row">
              ${asset.curated ? '<span class="badge curated">Curated</span>' : ""}
              ${asset.featured ? '<span class="badge">Featured</span>' : ""}
              <span class="badge">${asset.format}</span>
            </div>
          </div>
          <div class="asset-body">
            <div class="asset-title">
              <h3>${asset.title}</h3>
              <span class="price">${money(asset.price_cents)}</span>
            </div>
            <div class="meta-line">
              <span>${asset.category}</span>
              <span>${asset.engine}</span>
              <span>${asset.rating.toFixed(1)} rating</span>
            </div>
          </div>
        </button>
      </article>
    `
    )
    .join("");

  grid.querySelectorAll("[data-select]").forEach((button) => {
    button.addEventListener("click", () => selectAsset(button.dataset.select));
  });
}

function selectAsset(slug) {
  const asset = state.assets.find((item) => item.slug === slug);
  if (!asset) return;
  state.selected = asset;
  renderDetail(asset);
}

function renderDetail(asset) {
  const media = `<iframe src="${asset.preview_route}" width="100%" height="480" allow="autoplay; fullscreen; picture-in-picture; encrypted-media" allowfullscreen style="border:none; border-radius: 8px;" title="${asset.title} preview"></iframe>`;
  const downloadRoute = asset.download_route || "#";
  const downloadState = asset.download_route
    ? ""
    : ' aria-disabled="true" tabindex="-1"';

  $("#detailPanel").innerHTML = `
    <div class="detail-media">
      ${media}
    </div>
    <div class="detail-content">
      <div>
        <p class="eyebrow">${asset.category} / ${asset.format}</p>
        <h2>${asset.title}</h2>
      </div>
      <p>${asset.description}</p>
      <div class="spec-grid">
        <div><span>Creator</span><strong>${asset.creator.name}</strong></div>
        <div><span>License</span><strong>${asset.license_type}</strong></div>
        <div><span>Frames</span><strong>${asset.frames}</strong></div>
        <div><span>Resolution</span><strong>${asset.resolution}</strong></div>
        <div><span>Size</span><strong>${asset.file_size_mb} MB</strong></div>
        <div><span>Version</span><strong>${asset.version}</strong></div>
      </div>
      <div class="detail-actions">
        <button class="primary-action" type="button" id="addSelected">Add ${money(asset.price_cents)}</button>
        <a class="secondary-action download-action${asset.download_route ? "" : " disabled"}" href="${downloadRoute}" target="_blank" rel="noopener"${downloadState}>Download</a>
      </div>
    </div>
  `;
  $("#addSelected").addEventListener("click", () => addToCart(asset.slug));
}

function addToCart(slug) {
  const asset = state.assets.find((item) => item.slug === slug);
  if (!asset) return;
  const existing = state.cart.find((item) => item.slug === slug);
  if (existing) {
    existing.quantity += 1;
  } else {
    state.cart.push({ ...asset, quantity: 1 });
  }
  renderCart();
  openCart();
}

function renderCart() {
  $("#cartCount").textContent = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  $("#cartItems").innerHTML = state.cart.length
    ? state.cart
        .map(
          (item) => `
          <div class="cart-line">
            <div>
              <h3>${item.title}</h3>
              <p>${item.quantity} x ${money(item.price_cents)}</p>
            </div>
            <button class="icon-action" type="button" data-remove="${item.slug}" aria-label="Remove ${item.title}">x</button>
          </div>
        `
        )
        .join("")
    : '<div class="empty-grid">Cart is empty</div>';

  $("#cartItems").querySelectorAll("[data-remove]").forEach((button) => {
    button.addEventListener("click", () => {
      state.cart = state.cart.filter((item) => item.slug !== button.dataset.remove);
      renderCart();
    });
  });

  const total = state.cart.reduce((sum, item) => sum + item.quantity * item.price_cents, 0);
  $("#cartTotal").textContent = money(total);
}

function openCart() {
  $("#cartDrawer").classList.add("open");
  $("#cartDrawer").setAttribute("aria-hidden", "false");
}

function closeCart() {
  $("#cartDrawer").classList.remove("open");
  $("#cartDrawer").setAttribute("aria-hidden", "true");
}

async function checkout(event) {
  event.preventDefault();
  if (!state.cart.length) return;
  const form = new FormData(event.currentTarget);
  const order = await api("/api/orders", {
    method: "POST",
    body: JSON.stringify({
      buyer_email: form.get("buyer_email"),
      buyer_studio: form.get("buyer_studio"),
      plan: form.get("plan"),
      items: state.cart.map((item) => ({ slug: item.slug, quantity: item.quantity })),
    }),
  });
  $("#receipt").innerHTML = `
    Order #${order.id} paid: ${money(order.total_cents)}<br>
    Marketplace commission: ${money(order.commission_cents)}<br>
    ${order.items.length} download link${order.items.length === 1 ? "" : "s"} generated.
  `;
  state.cart = [];
  renderCart();
  await loadAssets();
}

async function uploadAsset(event) {
  event.preventDefault();
  const formEl =
    event.currentTarget ||
    event.target?.closest("form") ||
    document.getElementById("uploadForm");
  const form = new FormData(formEl);
  const tags = String(form.get("tags") || "")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
  form.set("price_cents", String(Math.round(Number(form.get("price")) * 100)));
  form.set("tags", JSON.stringify(tags));
  try {
    const asset = await api("/api/assets/upload", { method: "POST", body: form });
    $("#uploadStatus").textContent = `${asset.title} published.`;
    if (formEl && typeof formEl.reset === "function") {
      formEl.reset();
      updateFileName($("#previewFile"));
      updateFileName($("#sourceFile"));
    }
    await loadAssets();
    selectAsset(asset.slug);
  } catch (error) {
    $("#uploadStatus").textContent = error.message;
  }
}

function updateFileName(input) {
  const target = document.getElementById(`${input.id}Name`);
  target.textContent = input.files[0]?.name || "No file selected";
}

function hasExtension(file, extensions) {
  return extensions.some((extension) => file.name.toLowerCase().endsWith(extension));
}

function setupFileDropzone(inputId, extensions) {
  const input = document.getElementById(inputId);
  const dropzone = input.closest(".file-dropzone");

  const setFile = (file) => {
    if (!hasExtension(file, extensions)) {
      input.value = "";
      updateFileName(input);
      $("#uploadStatus").textContent = `Choose a ${extensions.join(" or ")} file.`;
      return;
    }
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    updateFileName(input);
    $("#uploadStatus").textContent = "";
  };

  input.addEventListener("change", () => {
    if (input.files[0]) setFile(input.files[0]);
  });
  ["dragenter", "dragover"].forEach((eventName) =>
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("is-dragover");
    })
  );
  ["dragleave", "drop"].forEach((eventName) =>
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("is-dragover");
    })
  );
  dropzone.addEventListener("drop", (event) => {
    const [file] = event.dataTransfer.files;
    if (file) setFile(file);
  });
}

async function loadPlans() {
  state.plans = await api("/api/plans");
  $("#planGrid").innerHTML = state.plans
    .map(
      (plan) => `
      <article class="plan-card">
        <h3>${plan.name}</h3>
        <p>${plan.benefit}</p>
        <strong>${plan.price_cents === null ? "Custom" : plan.price_cents ? money(plan.price_cents) : "Free"}</strong>
      </article>
    `
    )
    .join("");
}

async function sendEnterpriseInquiry(event) {
  event.preventDefault();
  const formEl = event.currentTarget || event.target?.closest("form");
  const form = new FormData(formEl);
  const payload = Object.fromEntries(form.entries());
  payload.seats = Number(payload.seats || 1);
  try {
    const inquiry = await api("/api/enterprise/inquiries", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    $("#enterpriseStatus").textContent = `Inquiry #${inquiry.id} received.`;
    if (formEl && typeof formEl.reset === "function") {
      formEl.reset();
    }
  } catch (error) {
    $("#enterpriseStatus").textContent = error.message;
  }
}

Object.values(filters).forEach((input) => {
  input.addEventListener("input", async () => {
    if (filters.q === input) {
      await fetchSearchResults(filters.q.value);
      return;
    }
    await loadAssets();
  });
});
$("#resetFilters").addEventListener("click", () => {
  filters.q.value = "";
  filters.category.value = "";
  filters.format.value = "";
  filters.engine.value = "";
  filters.sort.value = "featured";
  filters.curated.checked = false;
  loadAssets();
});
$("#cartToggle").addEventListener("click", openCart);
$("#cartClose").addEventListener("click", closeCart);
$("#checkoutForm").addEventListener("submit", checkout);
$("#uploadForm").addEventListener("submit", uploadAsset);
$("#enterpriseForm").addEventListener("submit", sendEnterpriseInquiry);
setupFileDropzone("previewFile", [".mov", ".mp4"]);
setupFileDropzone("sourceFile", [".vdb", ".zip"]);

renderCart();
loadPlans();
loadAssets();
