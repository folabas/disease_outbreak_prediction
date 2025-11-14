import { useEffect } from "react";
import AOS from "aos";
import "aos/dist/aos.css";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export const usePageAnimations = () => {
  useEffect(() => {
    // 1️⃣ Initialize AOS (Animate On Scroll)
    AOS.init({
      duration: 900,
      easing: "ease-out-cubic",
      once: false,
      offset: 100,
    });

    // Refresh AOS after page load
    setTimeout(() => AOS.refresh(), 400);

    // 2️⃣ GSAP Animations for sections
    const sections = gsap.utils.toArray<HTMLElement>(".fade-section");
    sections.forEach((section, i) => {
      gsap.fromTo(
        section,
        { opacity: 0, y: 40 },
        {
          opacity: 1,
          y: 0,
          duration: 0.9,
          delay: i * 0.1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: section,
            start: "top 80%",
            end: "bottom 10%",
            toggleActions: "play none none reverse",
          },
        }
      );
    });

    // 3️⃣ GSAP stagger for grids & cards
    const cards = gsap.utils.toArray<HTMLElement>(".fade-card");
    gsap.fromTo(
      cards,
      { opacity: 0, y: 20 },
      {
        opacity: 1,
        y: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: "power3.out",
        scrollTrigger: {
          trigger: ".fade-card",
          start: "top 90%",
        },
      }
    );
  }, []);
};
