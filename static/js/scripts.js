document.addEventListener('DOMContentLoaded', () => {
    // Set current year in footer
    const currentYear = document.getElementById('currentYear');
    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }

    // Mobile Menu Toggle
    const mobileToggle = document.getElementById('mobileToggle');
    const navMenu = document.getElementById('navMenu');
    const navOverlay = document.getElementById('navOverlay');
    if (mobileToggle && navMenu && navOverlay) {
        mobileToggle.addEventListener('click', () => {
            const isActive = navMenu.classList.toggle('active');
            navOverlay.classList.toggle('active', isActive);
            mobileToggle.innerHTML = isActive ? '<i class="fas fa-times"></i>' : '<i class="fas fa-bars"></i>';
            document.body.style.overflow = isActive ? 'hidden' : '';
        });
        
        navOverlay.addEventListener('click', () => {
            navMenu.classList.remove('active');
            navOverlay.classList.remove('active');
            mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
            document.body.style.overflow = '';
        });
        
        // Close menu on link click
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                if (navMenu.classList.contains('active')) {
                    navMenu.classList.remove('active');
                    navOverlay.classList.remove('active');
                    mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
                    document.body.style.overflow = '';
                }
            });
        });
    }

    // Dashboard Sidebar Toggle
    const toggleSidebar = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');
    const contentArea = document.getElementById('contentArea');
    if (toggleSidebar && sidebar && contentArea) {
        toggleSidebar.addEventListener('click', () => {
            const isActive = sidebar.classList.toggle('active');
            contentArea.classList.toggle('active', isActive);
            document.body.style.overflow = isActive ? 'hidden' : '';
            toggleSidebar.innerHTML = isActive ? '<i class="fas fa-times"></i>' : '<i class="fas fa-bars"></i>';
        });
    }

    // Scroll-triggered animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-in, .slide-up').forEach(element => {
        observer.observe(element);
    });

    // Dashboard Search Form Validation
    if (window.location.pathname.includes('/superuser/dashboard/')) {
        const searchForm = document.querySelector('.search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                const searchInput = searchForm.querySelector('input[name="q"]');
                if (searchInput && searchInput.value.trim() === '') {
                    e.preventDefault();
                    searchInput.focus();
                }
            });
        }
    }

    // Newsletter Form Submission
    const newsletterForm = document.getElementById('newsletterForm');
    const newsletterSuccess = document.getElementById('newsletterSuccess');
    if (newsletterForm && newsletterSuccess) {
        newsletterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const emailInput = newsletterForm.querySelector('.newsletter-input');
            if (emailInput && emailInput.value.trim() && /\S+@\S+\.\S+/.test(emailInput.value)) {
                newsletterSuccess.classList.add('visible');
                emailInput.value = '';
                setTimeout(() => {
                    newsletterSuccess.classList.remove('visible');
                }, 3000);
            } else if (emailInput) {
                emailInput.classList.add('error');
                setTimeout(() => {
                    emailInput.classList.remove('error');
                }, 2000);
            }
        });
    }

    // Auto-generate slug from title
    const titleInput = document.querySelector('#id_title');
    const slugInput = document.querySelector('#id_slug');
    if (titleInput && slugInput) {
        titleInput.addEventListener('input', () => {
            const slug = titleInput.value
                .toLowerCase()
                .replace(/[^a-z0-9\s-]/g, '')
                .replace(/\s+/g, '-')
                .replace(/-+/g, '-')
                .slice(0, 250);
            slugInput.value = slug;
        });
    }

    // Carousel Functionality
    const carousel = document.querySelector('.carousel');
    const slidesContainer = document.querySelector('.carousel-slides');
    const slides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.carousel-dot');
    const prevBtn = document.querySelector('.carousel-prev');
    const nextBtn = document.querySelector('.carousel-next');
    let currentSlide = 0;
    let autoSlideInterval;

    if (carousel && slidesContainer && slides.length && dots.length && prevBtn && nextBtn) {
        function showSlide(index) {
            if (index < 0 || index >= slides.length) return;
            slides.forEach((slide, i) => {
                slide.classList.toggle('active', i === index);
                if (dots[i]) {
                    dots[i].classList.toggle('active', i === index);
                }
            });
            currentSlide = index;
        }

        function nextSlide() {
            showSlide((currentSlide + 1) % slides.length);
        }

        function prevSlide() {
            showSlide((currentSlide - 1 + slides.length) % slides.length);
        }

        function startAutoSlide() {
            autoSlideInterval = setInterval(nextSlide, 5000);
        }

        function stopAutoSlide() {
            clearInterval(autoSlideInterval);
        }

        prevBtn.addEventListener('click', () => {
            stopAutoSlide();
            prevSlide();
            startAutoSlide();
        });

        nextBtn.addEventListener('click', () => {
            stopAutoSlide();
            nextSlide();
            startAutoSlide();
        });

        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                stopAutoSlide();
                showSlide(index);
                startAutoSlide();
            });
        });

        carousel.addEventListener('mouseenter', stopAutoSlide);
        carousel.addEventListener('mouseleave', startAutoSlide);

        showSlide(0);
        startAutoSlide();
    }
});