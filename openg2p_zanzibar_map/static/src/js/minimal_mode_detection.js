(function () {
    const DASHBOARD_ACTION_HASH = '#action=openg2p_zanzibar_map.sr_dashboard_action';

    /**
     * Try to get session info from all known Odoo paths.
     * Odoo 17 typically uses window.odoo.__session_info__
     */
    const getSessionInfo = () => {
        if (window.odoo) {
            return window.odoo.__session_info__ || window.odoo.session_info || null;
        }
        return null;
    };

    const applyMinimalMode = () => {
        if (!document.body) {
            setTimeout(applyMinimalMode, 10);
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const minimalParam = urlParams.get('minimal');
        
        // 1. Detection and Persistence
        if (minimalParam === '1') {
            sessionStorage.setItem('o_minimal_view', '1');
        } else if (minimalParam === '0') {
            sessionStorage.removeItem('o_minimal_view');
            sessionStorage.removeItem('o_minimal_no_access');
            sessionStorage.removeItem('o_dashboard_wrong_url');
        }

        const sessionInfo = getSessionInfo();
        const isMinimalSession = sessionStorage.getItem('o_minimal_view') === '1';

        // 2. Dashboard Viewer on DEFAULT URL (no ?minimal=1)
        // This user MUST use the minimal URL. Block them entirely.
        if (sessionInfo && sessionInfo.is_dashboard_standalone && !isMinimalSession) {
            sessionStorage.setItem('o_dashboard_wrong_url', '1');
            document.body.classList.add('o_minimal_view');

            const hideSelectors = ['.o_main_navbar', '.o_navbar', 'header', '.o_header'];
            hideSelectors.forEach(selector => {
                const el = document.querySelector(selector);
                if (el) {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                }
            });

            const isLoginPage = window.location.pathname.includes('/web/login');
            if (isLoginPage) return; // Only capture flag on login page, don't hide/redirect yet

            const currentHash = window.location.hash;
            const isOnDashboard = currentHash.includes('z_dashboard_main') ||
                                  currentHash.includes('sr_dashboard_action');
            if (!isOnDashboard) {
                window.location.hash = DASHBOARD_ACTION_HASH;
            }
            return;
        }

        // 3. Dashboard Viewer on MINIMAL URL — grant access, clear wrong-url flag
        if (sessionInfo && sessionInfo.is_dashboard_standalone && isMinimalSession) {
            sessionStorage.removeItem('o_dashboard_wrong_url');
        }

        // 4. Access Control Check for non-dashboard-viewer on ?minimal=1
        if (isMinimalSession) {
            if (sessionInfo && typeof sessionInfo.is_dashboard_viewer !== 'undefined') {
                if (!sessionInfo.is_dashboard_viewer) {
                    sessionStorage.setItem('o_minimal_no_access', '1');
                } else {
                    sessionStorage.removeItem('o_minimal_no_access');
                }
            }
        }

        // 5. Determine if user should be locked to dashboard only
        const isLocked = sessionStorage.getItem('o_minimal_no_access') === '1' ||
                         sessionStorage.getItem('o_dashboard_wrong_url') === '1';

        // 6. Application: Apply minimal mode UI
        if (isMinimalSession || isLocked) {
            document.body.classList.add('o_minimal_view');
            
            const hideSelectors = ['.o_main_navbar', '.o_navbar', 'header', '.o_header'];
            hideSelectors.forEach(selector => {
                const el = document.querySelector(selector);
                if (el) {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                }
            });

            const currentHash = window.location.hash;
            const isOnDashboard = currentHash.includes('z_dashboard_main') || 
                                  currentHash.includes('sr_dashboard_action');

            if (isLocked) {
                if (!isOnDashboard) {
                    window.location.hash = DASHBOARD_ACTION_HASH;
                }
            } else {
                if (!currentHash || currentHash === '#' || currentHash === '#home') {
                    window.location.hash = DASHBOARD_ACTION_HASH;
                }
            }
        }
    };

    // 7. GUARD: Intercept hash changes to prevent locked users from navigating
    window.addEventListener('hashchange', () => {
        const isLocked = sessionStorage.getItem('o_minimal_no_access') === '1' ||
                         sessionStorage.getItem('o_dashboard_wrong_url') === '1';

        if (isLocked) {
            const newHash = window.location.hash;
            const isOnDashboard = newHash.includes('z_dashboard_main') || 
                                  newHash.includes('sr_dashboard_action');
            if (!isOnDashboard) {
                window.location.hash = DASHBOARD_ACTION_HASH;
            }
        }
    });

    applyMinimalMode();
    setInterval(applyMinimalMode, 100);
})();
