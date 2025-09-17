(function () {
    const animatedElements = document.querySelectorAll(".animate-fade-up, [data-animate]");

    animatedElements.forEach((el) => {
        const delay = el.dataset.animateDelay;
        if (delay) {
            el.style.transitionDelay = delay;
            el.style.animationDelay = delay;
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
            parallaxTargets.forEach((target) => {
                const intensity = parseFloat(target.dataset.parallax || "0.25");
                const offset = window.scrollY * intensity;
                target.style.transform = `translate3d(0, ${offset}px, 0)`;
            });
        };
        handleParallax();
        window.addEventListener("scroll", handleParallax, { passive: true });
    }
})();
