(function () {
    const animatedElements = document.querySelectorAll(".animate-fade-up");

    if (!("IntersectionObserver" in window)) {
        animatedElements.forEach((el) => el.classList.add("is-visible"));
        return;
    }

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
})();
