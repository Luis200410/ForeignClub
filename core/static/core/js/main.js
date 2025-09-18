(function () {
    const animatedElements = document.querySelectorAll(".animate-fade-up, [data-animate]");

    animatedElements.forEach((el) => {
        const delay = el.dataset.animateDelay;
        if (delay) {
            el.style.transitionDelay = delay;
            el.style.animationDelay = delay;
            el.style.setProperty("--animate-delay", delay);
        }
    });

    if (!("IntersectionObserver" in window)) {
        animatedElements.forEach((el) => el.classList.add("is-visible"));
    } else {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                rootMargin: "0px 0px -10% 0px",
                threshold: 0.2,
            }
        );

        animatedElements.forEach((el) => observer.observe(el));
    }

    const parallaxTargets = document.querySelectorAll("[data-parallax]");
    if (parallaxTargets.length) {
        const handleParallax = () => {
            const scrollY = window.scrollY;
            parallaxTargets.forEach((target) => {
                const intensity = parseFloat(target.dataset.parallax || "0.25");
                const offset = scrollY * intensity;
                target.style.transform = `translate3d(0, ${offset}px, 0)`;
            });
        };
        handleParallax();
        window.addEventListener("scroll", handleParallax, { passive: true });
    }

    const tiltTargets = document.querySelectorAll("[data-tilt]");
    if (tiltTargets.length) {
        tiltTargets.forEach((target) => {
            const strength = parseFloat(target.dataset.tilt || "6");
            const updateTilt = (event) => {
                const rect = target.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const percentX = (event.clientX - centerX) / (rect.width / 2);
                const percentY = (event.clientY - centerY) / (rect.height / 2);
                target.style.setProperty('--tilt-rotate-x', `${percentY * -strength}deg`);
                target.style.setProperty('--tilt-rotate-y', `${percentX * strength}deg`);
            };

            const resetTilt = () => {
                target.style.setProperty('--tilt-rotate-x', '0deg');
                target.style.setProperty('--tilt-rotate-y', '0deg');
            };

            target.addEventListener("mousemove", updateTilt);
            target.addEventListener("mouseleave", resetTilt);
        });
    }
})();
