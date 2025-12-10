/**
 * Dashboard Navigation Component
 */
export class Navbar {
    constructor() {
        this.currentSection = 'settings';
    }

    render() {
        return `
            <nav class="dashboard-nav">
                <ul>
                    <li><a href="#settings" data-section="settings">Settings</a></li>
                    <li><a href="#logs" data-section="logs">Logs</a></li>
                    <li><a href="#reservations" data-section="reservations">Reservations</a></li>
                    <li><a href="#logout" data-section="logout">Logout</a></li>
                </ul>
            </nav>
        `;
    }

    attachListeners() {
        document.querySelectorAll('a[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.dataset.section;
                this.navigateToSection(section);
            });
        });
    }

    navigateToSection(section) {
        this.currentSection = section;
        // Emit event or update view
        window.dispatchEvent(new CustomEvent('sectionChange', { detail: { section } }));
    }
}


