class SmoothScroll {
    constructor() {
        this.bindMethods();

        this.data = {
            ease: 0.08,
            current: 0,
            last: 0,
            rounded: 0
        };

        this.dom = {
            el: document.querySelector('#smooth-wrapper'),
            content: document.querySelector('#smooth-content')
        };

        if (!this.dom.el) return;

        this.rAF = null;
        this.init();
    }

    bindMethods() {
        this.run = this.run.bind(this);
        this.resize = this.resize.bind(this);
    }

    setStyles() {
        Object.assign(this.dom.el.style, {
            position: 'fixed',
            top: 0,
            left: 0,
            height: '100%',
            width: '100%',
            overflow: 'hidden'
        });
    }

    setHeight() {
        document.body.style.height = `${this.dom.content.getBoundingClientRect().height}px`;
    }

    resize() {
        this.setHeight();
        this.scroll();
    }

    scroll() {
        this.data.current = window.scrollY;
    }

    run() {
        this.data.last += (this.data.current - this.data.last) * this.data.ease;
        this.data.rounded = Math.round(this.data.last * 100) / 100;

        const diff = this.data.current - this.data.rounded;
        const acc = diff / window.innerWidth;
        const velo = + acc;
        const skew = velo * 7.5;

        this.dom.content.style.transform = `translate3d(0, -${this.data.rounded}px, 0) skewY(${skew}deg)`;

        this.requestAnimationFrame();
    }

    init() {
        this.on();
        // Add ResizeObserver to handle dynamic content changes
        this.resizeObserver = new ResizeObserver(() => this.resize());
        this.resizeObserver.observe(this.dom.content);
    }

    on() {
        this.setStyles();
        this.setHeight();
        this.addEvents();
        this.requestAnimationFrame();
    }

    off() {
        this.cancelAnimationFrame();
        this.removeEvents();
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
    }

    requestAnimationFrame() {
        this.rAF = requestAnimationFrame(this.run);
    }

    cancelAnimationFrame() {
        cancelAnimationFrame(this.rAF);
    }

    addEvents() {
        window.addEventListener('resize', this.resize, { passive: true });
        window.addEventListener('scroll', this.scroll, { passive: true });
    }

    removeEvents() {
        window.removeEventListener('resize', this.resize, { passive: true });
        window.removeEventListener('scroll', this.scroll, { passive: true });
    }
}

class KineticInteractions {
    constructor() {
        this.initCursor();
        this.initObservers();
        this.initHorizontalScroll();
    }

    initCursor() {
        const cursorDot = document.createElement('div');
        const cursorCircle = document.createElement('div');
        cursorDot.className = 'cursor-dot';
        cursorCircle.className = 'cursor-circle';
        document.body.appendChild(cursorDot);
        document.body.appendChild(cursorCircle);

        let mouseX = 0, mouseY = 0;
        let circleX = 0, circleY = 0;

        window.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;

            cursorDot.style.transform = `translate3d(${mouseX - 10}px, ${mouseY - 10}px, 0)`;
        });

        const animateCircle = () => {
            circleX += (mouseX - circleX) * 0.15;
            circleY += (mouseY - circleY) * 0.15;

            cursorCircle.style.transform = `translate3d(${circleX - 30}px, ${circleY - 30}px, 0)`;
            requestAnimationFrame(animateCircle);
        };
        animateCircle();

        // Hover states
        const links = document.querySelectorAll('a, button, .hover-trigger');
        links.forEach(link => {
            link.addEventListener('mouseenter', () => {
                cursorCircle.style.transform = `translate3d(${circleX - 30}px, ${circleY - 30}px, 0) scale(1.5)`;
                cursorCircle.style.borderColor = 'transparent';
                cursorCircle.style.backgroundColor = 'rgba(204, 255, 0, 0.2)';
            });
            link.addEventListener('mouseleave', () => {
                cursorCircle.style.transform = `translate3d(${circleX - 30}px, ${circleY - 30}px, 0) scale(1)`;
                cursorCircle.style.borderColor = 'var(--primary)';
                cursorCircle.style.backgroundColor = 'transparent';
            });
        });
    }

    initObservers() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-in-view');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('[data-scroll]').forEach(el => observer.observe(el));
    }

    initHorizontalScroll() {
        const section = document.querySelector('.horizontal-scroll-section');
        const track = document.querySelector('.horizontal-track');

        if (!section || !track) return;

        window.addEventListener('scroll', () => {
            const rect = section.getBoundingClientRect();
            const offset = -rect.top;
            const maxScroll = section.offsetHeight - window.innerHeight;

            if (offset > 0 && offset < maxScroll) {
                const percent = offset / maxScroll;
                const move = -(track.scrollWidth - window.innerWidth) * percent;
                track.style.transform = `translateX(${move}px)`;
            }
        });
    }
}

// Init
window.onload = () => {
    // Native scroll is used now for reliability
    new KineticInteractions();
};
