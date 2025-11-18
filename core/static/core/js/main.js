(function () {
    const animatedElements = document.querySelectorAll("[data-animate]");

    animatedElements.forEach((el) => {
        const delay = el.dataset.animateDelay;
        if (delay) {
            el.style.transitionDelay = delay;
            el.style.animationDelay = delay;
            el.style.setProperty("--animate-delay", delay);
        }
    });

    if ("IntersectionObserver" in window) {
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
    } else {
        animatedElements.forEach((el) => el.classList.add("is-visible"));
    }

    const tiltTargets = document.querySelectorAll("[data-tilt]");
    tiltTargets.forEach((target) => {
        const strength = parseFloat(target.dataset.tilt || "6");
        const updateTilt = (event) => {
            const rect = target.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const percentX = Math.max(-1, Math.min(1, (event.clientX - centerX) / (rect.width / 2)));
            const percentY = Math.max(-1, Math.min(1, (event.clientY - centerY) / (rect.height / 2)));
            target.style.setProperty("--tilt-rotate-x", `${percentY * -strength}deg`);
            target.style.setProperty("--tilt-rotate-y", `${percentX * strength}deg`);
        };

        const resetTilt = () => {
            target.style.setProperty("--tilt-rotate-x", "0deg");
            target.style.setProperty("--tilt-rotate-y", "0deg");
        };

        target.addEventListener("mousemove", updateTilt);
        target.addEventListener("mouseleave", resetTilt);
    });

    const magneticItems = document.querySelectorAll("[data-magnetic]");
    magneticItems.forEach((item) => {
        const strength = parseFloat(item.dataset.magneticStrength || "14");
        const handleMove = (event) => {
            const rect = item.getBoundingClientRect();
            const offsetX = event.clientX - (rect.left + rect.width / 2);
            const offsetY = event.clientY - (rect.top + rect.height / 2);
            const translateX = (offsetX / rect.width) * strength;
            const translateY = (offsetY / rect.height) * strength;
            item.style.setProperty("--magnetic-x", `${translateX}px`);
            item.style.setProperty("--magnetic-y", `${translateY}px`);
            item.classList.add("is-hovering");
        };

        const resetMove = () => {
            item.style.setProperty("--magnetic-x", "0px");
            item.style.setProperty("--magnetic-y", "0px");
            item.classList.remove("is-hovering");
        };

        item.addEventListener("mousemove", handleMove);
        item.addEventListener("mouseleave", resetMove);
        item.addEventListener("blur", resetMove);
        item.addEventListener("touchstart", resetMove, { passive: true });
    });

    const sliders = document.querySelectorAll("[data-slider]");
    sliders.forEach((slider) => {
        const track = slider.querySelector("[data-slider-track]");
        const prev = slider.querySelector("[data-slider-prev]");
        const next = slider.querySelector("[data-slider-next]");
        if (!track) {
            return;
        }

        const getScrollAmount = () => {
            const firstSlide = track.querySelector(":scope > *");
            if (!firstSlide) {
                return track.clientWidth;
            }
            const style = window.getComputedStyle(track);
            const gap = parseFloat(style.columnGap || style.gap || "0");
            return firstSlide.getBoundingClientRect().width + gap;
        };

        const clampScroll = (value) => {
            const maxScroll = Math.max(0, track.scrollWidth - track.clientWidth);
            return Math.min(Math.max(value, 0), maxScroll);
        };

        const updateButtons = () => {
            if (!prev || !next) {
                return;
            }
            const maxScroll = Math.max(0, track.scrollWidth - track.clientWidth - 1);
            prev.disabled = track.scrollLeft <= 0;
            next.disabled = track.scrollLeft >= maxScroll;
        };

        const moveSlider = (direction) => {
            const amount = getScrollAmount();
            const target = direction === "next"
                ? clampScroll(track.scrollLeft + amount)
                : clampScroll(track.scrollLeft - amount);
            track.scrollTo({ left: target, behavior: "smooth" });
            window.requestAnimationFrame(() => setTimeout(updateButtons, 220));
        };

        if (prev) {
            prev.addEventListener("click", () => moveSlider("prev"));
        }
        if (next) {
            next.addEventListener("click", () => moveSlider("next"));
        }

        track.addEventListener("scroll", updateButtons, { passive: true });
        window.addEventListener("resize", updateButtons);
        updateButtons();
    });
})();
