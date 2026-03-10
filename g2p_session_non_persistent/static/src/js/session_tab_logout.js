/** @odoo-module **/

const TAB_COUNT_KEY = "g2p_odoo_open_tabs_count";
const IDLE_TIMEOUT = 300 * 1000; // 5 minutes in milliseconds

function getTabCount() {
    return parseInt(localStorage.getItem(TAB_COUNT_KEY) || "0", 10);
}

function setTabCount(count) {
    localStorage.setItem(TAB_COUNT_KEY, Math.max(0, count).toString());
}

let idleTimer;

function resetIdleTimer() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        window.location.href = "/web/session/logout";
    }, IDLE_TIMEOUT);
}

// 1. Initial Load: Increment count and cancel any pending logout
(function init() {
    const currentCount = getTabCount();
    setTabCount(currentCount + 1);

    // Always try to cancel any pending logout on load
    fetch("/web/session/tab_logout/cancel");

    // Start Idle Monitoring
    resetIdleTimer();
    window.addEventListener("mousemove", resetIdleTimer);
    window.addEventListener("keydown", resetIdleTimer);
    window.addEventListener("click", resetIdleTimer);
    window.addEventListener("scroll", resetIdleTimer);
})();

// 2. Tab Close: Decrement count and request logout if this was the last tab
window.addEventListener("beforeunload", () => {
    const newCount = getTabCount() - 1;
    setTabCount(newCount);

    if (newCount <= 0) {
        const formData = new FormData();
        if (window.odoo && window.odoo.csrf_token) {
            formData.append("csrf_token", window.odoo.csrf_token);
        }
        navigator.sendBeacon("/web/session/tab_logout/request", formData);
    }
});
