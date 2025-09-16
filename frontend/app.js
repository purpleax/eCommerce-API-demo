const API_BASE = window.API_BASE_URL || `${window.location.origin}/api`;

const state = {
  token: localStorage.getItem('token') || null,
  user: null,
  products: [],
  cart: { items: [], subtotal: 0 },
  orders: [],
};

const messageEl = document.getElementById('message');
const userEmailEl = document.getElementById('user-email');
const logoutBtn = document.getElementById('logout-btn');
const authSection = document.getElementById('auth-section');
const adminSection = document.getElementById('admin-section');
const productGrid = document.getElementById('product-grid');
const cartItemsEl = document.getElementById('cart-items');
const cartSubtotalEl = document.getElementById('cart-subtotal');
const checkoutBtn = document.getElementById('checkout-btn');
const ordersEl = document.getElementById('orders');

function formToJSON(form) {
  const data = {};
  const formData = new FormData(form);
  for (const [key, value] of formData.entries()) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      const current = data[key];
      data[key] = Array.isArray(current) ? current.concat(value) : [current, value];
    } else {
      data[key] = value;
    }
  }
  return { data, formData };
}

function setMessage(text, variant = 'info') {
  messageEl.textContent = text || '';
  messageEl.dataset.variant = variant;
}

async function apiRequest(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {};
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type');
  const data = contentType && contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const errorMessage = typeof data === 'string' ? data : data?.detail || 'Request failed';
    throw new Error(errorMessage);
  }

  return data;
}

function storeToken(token) {
  if (token) {
    state.token = token;
    localStorage.setItem('token', token);
  } else {
    state.token = null;
    localStorage.removeItem('token');
  }
}

async function loadProfile() {
  if (!state.token) {
    state.user = null;
    updateAuthUI();
    return;
  }
  try {
    const profile = await apiRequest('/users/me');
    state.user = profile;
    updateAuthUI();
    await Promise.all([loadProducts(), loadCart(), loadOrders()]);
  } catch (error) {
    console.error('Profile load failed', error);
    storeToken(null);
    setMessage('Session expired. Please log in again.', 'error');
    updateAuthUI();
  }
}

function formatCurrency(amount) {
  const number = Number(amount);
  if (Number.isNaN(number)) {
    return '$0.00';
  }
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
  }).format(number);
}

function updateAuthUI() {
  if (state.user) {
    userEmailEl.textContent = state.user.email;
    authSection.hidden = true;
    logoutBtn.hidden = false;
    checkoutBtn.disabled = state.cart.items.length === 0;
    if (state.user.is_admin) {
      adminSection.hidden = false;
    } else {
      adminSection.hidden = true;
    }
  } else {
    userEmailEl.textContent = 'Guest';
    authSection.hidden = false;
    logoutBtn.hidden = true;
    adminSection.hidden = true;
    checkoutBtn.disabled = true;
    state.cart = { items: [], subtotal: 0 };
    renderCart();
    renderOrders();
  }
}

async function loadProducts() {
  try {
    const products = await apiRequest('/products');
    state.products = products;
    renderProducts();
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

function renderProducts() {
  productGrid.innerHTML = '';
  state.products.forEach((product) => {
    const card = document.createElement('article');
    card.className = 'product-card';
    card.innerHTML = `
      ${product.image_url ? `<img src="${product.image_url}" alt="${product.name}" />` : ''}
      <h3>${product.name}</h3>
      <p>${product.description}</p>
      <div class="price">${formatCurrency(product.price)}</div>
      <div>In stock: ${product.inventory_count}</div>
      <div class="card-actions"></div>
    `;

    const actions = card.querySelector('.card-actions');
    const addButton = document.createElement('button');
    addButton.textContent = 'Add to cart';
    addButton.addEventListener('click', () => handleAddToCart(product.id));
    addButton.disabled = !state.user;
    actions.appendChild(addButton);

    if (state.user?.is_admin) {
      const editButton = document.createElement('button');
      editButton.className = 'secondary';
      editButton.textContent = 'Edit';
      editButton.addEventListener('click', () => populateProductForm(product));
      const deleteButton = document.createElement('button');
      deleteButton.className = 'secondary';
      deleteButton.textContent = 'Delete';
      deleteButton.addEventListener('click', () => handleDeleteProduct(product.id));
      actions.append(editButton, deleteButton);
    }

    productGrid.appendChild(card);
  });
}

async function handleAddToCart(productId) {
  if (!state.user) {
    setMessage('Login required to add items to the cart.', 'error');
    return;
  }
  try {
    await apiRequest('/cart/items', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity: 1 }),
    });
    setMessage('Item added to cart.');
    await loadCart();
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

async function loadCart() {
  if (!state.user) return;
  try {
    const cart = await apiRequest('/cart');
    state.cart = cart;
    renderCart();
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

function renderCart() {
  cartItemsEl.innerHTML = '';
  if (!state.cart.items || state.cart.items.length === 0) {
    cartItemsEl.innerHTML = '<p>Your cart is empty.</p>';
    cartSubtotalEl.textContent = formatCurrency(0);
    checkoutBtn.disabled = true;
    return;
  }
  state.cart.items.forEach((item) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'cart-item';
    wrapper.innerHTML = `
      <header>
        <h3>${item.product.name}</h3>
        <span>${formatCurrency(item.product.price)}</span>
      </header>
      <div class="cart-item-controls">
        <label>
          Qty
          <input type="number" min="1" value="${item.quantity}" data-item-id="${item.id}" />
        </label>
        <button data-action="update" data-item-id="${item.id}">Update</button>
        <button class="secondary" data-action="remove" data-item-id="${item.id}">Remove</button>
      </div>
    `;
    cartItemsEl.appendChild(wrapper);
  });
  cartSubtotalEl.textContent = formatCurrency(state.cart.subtotal);
  checkoutBtn.disabled = false;
}

cartItemsEl.addEventListener('click', async (event) => {
  const action = event.target.dataset.action;
  if (!action) return;
  const itemId = Number(event.target.dataset.itemId);
  const input = cartItemsEl.querySelector(`input[data-item-id="${itemId}"]`);
  if (action === 'update') {
    const quantity = Number(input.value);
    if (!Number.isInteger(quantity) || quantity < 1) {
      setMessage('Quantity must be at least 1', 'error');
      return;
    }
    try {
      await apiRequest(`/cart/items/${itemId}`, {
        method: 'PUT',
        body: JSON.stringify({ quantity }),
      });
      setMessage('Cart updated.');
      await loadCart();
    } catch (error) {
      setMessage(error.message, 'error');
    }
  } else if (action === 'remove') {
    try {
      await apiRequest(`/cart/items/${itemId}`, { method: 'DELETE' });
      setMessage('Item removed.');
      await loadCart();
    } catch (error) {
      setMessage(error.message, 'error');
    }
  }
});

checkoutBtn.addEventListener('click', async () => {
  if (!state.user) return;
  try {
    await apiRequest('/orders', { method: 'POST', body: JSON.stringify({}) });
    setMessage('Order placed successfully.');
    await Promise.all([loadCart(), loadOrders()]);
  } catch (error) {
    setMessage(error.message, 'error');
  }
});

async function loadOrders() {
  if (!state.user) return;
  try {
    const orders = await apiRequest('/orders');
    state.orders = orders;
    renderOrders();
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

function renderOrders() {
  ordersEl.innerHTML = '';
  if (!state.orders.length) {
    ordersEl.innerHTML = '<p>No orders yet.</p>';
    return;
  }
  state.orders.forEach((order) => {
    const card = document.createElement('article');
    card.className = 'order-card';
    card.innerHTML = `
      <header class="section-header">
        <div>
          <h3>Order #${order.id}</h3>
          <p>${new Date(order.created_at).toLocaleString()}</p>
        </div>
        <strong>${formatCurrency(order.total_amount)}</strong>
      </header>
      <div class="order-items">
        ${order.items
          .map(
            (item) => `
              <div>
                ${item.product.name} &times; ${item.quantity}
                <span>(${formatCurrency(item.unit_price)})</span>
              </div>
            `,
          )
          .join('')}
      </div>
    `;
    ordersEl.appendChild(card);
  });
}

const registerForm = document.getElementById('register-form');
registerForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const { data, formData } = formToJSON(registerForm);
  const payload = {
    email: data.email,
    full_name: data.full_name || null,
    password: data.password,
    is_admin: formData.get('is_admin') === 'on',
  };
  try {
    await apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    setMessage('Registration successful. You can now log in.');
    registerForm.reset();
  } catch (error) {
    setMessage(error.message, 'error');
  }
});

const loginForm = document.getElementById('login-form');
loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const { data } = formToJSON(loginForm);
  const payload = {
    email: data.email,
    password: data.password,
  };
  try {
    const token = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    storeToken(token.access_token);
    setMessage('Logged in successfully.');
    loginForm.reset();
    await loadProfile();
  } catch (error) {
    setMessage(error.message, 'error');
  }
});

logoutBtn.addEventListener('click', () => {
  storeToken(null);
  state.user = null;
  updateAuthUI();
  setMessage('Logged out.');
  loadProducts();
});

const productForm = document.getElementById('product-form');
productForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!state.user?.is_admin) return;
  const { data, formData } = formToJSON(productForm);
  const productId = data.product_id || null;
  const payload = {
    name: data.name,
    description: data.description,
    price: Number(data.price),
    inventory_count: Number(data.inventory_count),
    image_url: data.image_url || null,
    is_active: formData.get('is_active') === 'on',
  };

  const method = productId ? 'PUT' : 'POST';
  const endpoint = productId ? `/products/${productId}` : '/products';
  try {
    await apiRequest(endpoint, {
      method,
      body: JSON.stringify(payload),
    });
    setMessage(productId ? 'Product updated.' : 'Product created.');
    productForm.reset();
    loadProducts();
  } catch (error) {
    setMessage(error.message, 'error');
  }
});

function populateProductForm(product) {
  const form = productForm;
  form.product_id.value = product.id;
  form.name.value = product.name;
  form.description.value = product.description;
  form.price.value = product.price;
  form.inventory_count.value = product.inventory_count;
  form.image_url.value = product.image_url || '';
  form.is_active.checked = product.is_active;
  form.scrollIntoView({ behavior: 'smooth' });
}

const resetProductBtn = document.getElementById('reset-product');
resetProductBtn.addEventListener('click', () => {
  productForm.reset();
});

async function handleDeleteProduct(productId) {
  if (!state.user?.is_admin) return;
  const confirmed = confirm('Delete this product?');
  if (!confirmed) return;
  try {
    await apiRequest(`/products/${productId}`, { method: 'DELETE' });
    setMessage('Product deleted.');
    loadProducts();
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

// Refresh buttons

document.getElementById('refresh-products').addEventListener('click', loadProducts);
document.getElementById('refresh-cart').addEventListener('click', loadCart);
document.getElementById('refresh-orders').addEventListener('click', loadOrders);

// Bootstrap on load
(async function bootstrap() {
  await loadProducts();
  await loadProfile();
})();
