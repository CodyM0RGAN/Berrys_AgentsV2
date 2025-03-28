/**
 * Main JavaScript file for Berry's Agents
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize tooltips
    initTooltips();

    // Initialize popovers
    initPopovers();

    // Add event listeners for sidebar toggle (if exists)
    initSidebarToggle();

    // Initialize any charts on the page
    initCharts();

    // Add fade-in animation to cards
    animateCards();

    // Initialize form validation
    initFormValidation();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Initialize sidebar toggle functionality
 */
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function (e) {
            e.preventDefault();
            document.body.classList.toggle('sidebar-collapsed');
        });
    }
}

/**
 * Initialize charts if Chart.js is available
 */
function initCharts() {
    if (typeof Chart !== 'undefined') {
        // Find all canvas elements with chart data
        const chartElements = document.querySelectorAll('canvas[data-chart]');

        chartElements.forEach(function (canvas) {
            const chartType = canvas.getAttribute('data-chart-type') || 'line';
            const chartData = JSON.parse(canvas.getAttribute('data-chart'));

            new Chart(canvas, {
                type: chartType,
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        });
    }
}

/**
 * Add fade-in animation to cards
 */
function animateCards() {
    const cards = document.querySelectorAll('.card:not(.no-animation)');

    cards.forEach(function (card, index) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';

        // Stagger the animations
        setTimeout(function () {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index);
    });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');

    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Format a date string
 * @param {string} dateString - The date string to format
 * @param {boolean} includeTime - Whether to include the time
 * @returns {string} The formatted date string
 */
function formatDate(dateString, includeTime = false) {
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };

    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }

    return date.toLocaleDateString('en-US', options);
}

/**
 * Format a number as a percentage
 * @param {number} value - The value to format
 * @param {number} decimals - The number of decimal places
 * @returns {string} The formatted percentage
 */
function formatPercent(value, decimals = 0) {
    return value.toFixed(decimals) + '%';
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of toast (success, error, warning, info)
 * @param {number} duration - The duration in milliseconds
 */
function showToast(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    // Create toast content
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    // Add toast to container
    toastContainer.appendChild(toastEl);

    // Initialize and show toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: duration
    });

    toast.show();

    // Remove toast element after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function () {
        toastEl.remove();
    });
}

/**
 * Confirm an action with a modal dialog
 * @param {string} message - The confirmation message
 * @param {Function} callback - The callback function to execute if confirmed
 * @param {string} title - The title of the confirmation dialog
 */
function confirmAction(message, callback, title = 'Confirm Action') {
    // Create modal element
    const modalEl = document.createElement('div');
    modalEl.className = 'modal fade';
    modalEl.id = 'confirmActionModal';
    modalEl.setAttribute('tabindex', '-1');
    modalEl.setAttribute('aria-labelledby', 'confirmActionModalLabel');
    modalEl.setAttribute('aria-hidden', 'true');

    // Create modal content
    modalEl.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="confirmActionModalLabel">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    ${message}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="confirmActionBtn">Confirm</button>
                </div>
            </div>
        </div>
    `;

    // Add modal to body
    document.body.appendChild(modalEl);

    // Initialize modal
    const modal = new bootstrap.Modal(modalEl);

    // Add event listener to confirm button
    const confirmBtn = document.getElementById('confirmActionBtn');
    confirmBtn.addEventListener('click', function () {
        modal.hide();
        callback();
    });

    // Remove modal element after it's hidden
    modalEl.addEventListener('hidden.bs.modal', function () {
        modalEl.remove();
    });

    // Show modal
    modal.show();
}
