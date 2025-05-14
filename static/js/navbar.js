// JavaScript for Modern Navigation Bar

document.addEventListener('DOMContentLoaded', function() {
    // Navbar scroll effect with improved performance
    const navbar = document.querySelector('.modern-navbar');

    if (navbar) {
        // Use requestAnimationFrame for smoother scrolling effect
        let lastScrollY = window.scrollY;
        let ticking = false;

        window.addEventListener('scroll', function() {
            lastScrollY = window.scrollY;

            if (!ticking) {
                window.requestAnimationFrame(function() {
                    if (lastScrollY > 30) {
                        navbar.classList.add('scrolled');
                    } else {
                        navbar.classList.remove('scrolled');
                    }
                    ticking = false;
                });

                ticking = true;
            }
        });

        // Initial check for page load with scroll already happened
        if (window.scrollY > 30) {
            navbar.classList.add('scrolled');
        }
    }

    // Dropdown menu animation if using animate.css
    const dropdownMenus = document.querySelectorAll('.dropdown-menu');

    dropdownMenus.forEach(menu => {
        if (typeof menu.classList.add === 'function') {
            menu.classList.add('animate__animated', 'animate__fadeInDown');
        }
    });

    // Mobile menu improvements
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    const navbarToggler = document.querySelector('.navbar-toggler');

    // Close mobile menu when clicking on a link
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992 && navbarCollapse && navbarCollapse.classList.contains('show')) {
                navbarToggler.click();
            }
        });
    });

    // Search functionality removed

    // Add active class based on current page
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath && currentPath === linkPath) {
            link.classList.add('active');
        }
    });
});
