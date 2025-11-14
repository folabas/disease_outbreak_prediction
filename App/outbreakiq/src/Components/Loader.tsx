import { useEffect } from "react";
import { gsap } from "gsap";
import { motion } from "framer-motion";


const Loader: React.FC = () => {
  useEffect(() => {
    const bars = gsap.utils.toArray<HTMLElement>(".loader-bar");

    const tl = gsap.timeline({ repeat: -1, repeatDelay: 0.8 });

    tl.fromTo(
      bars,
      { scaleY: 0 },
      {
        scaleY: 1,
        transformOrigin: "bottom center",
        duration: 1.25,
        stagger: 0.18,
        ease: "power2.out",
      }
    );

    // 2️⃣ Bars retract together
    tl.to(
      bars,
      {
        scaleY: 0,
        duration: 0.4,
        ease: "power2.inOut",
        stagger: 0.1,
      },
      "+=0.6"
    );

    return () => tl.kill();
  }, []);

  return (
    <div className="h-screen w-full flex flex-col items-center justify-center bg-gray-300 overflow-hidden">
      {/* Bars */}
      <div className="flex items-end justify-center gap-2 sm:gap-3 md:gap-4 mb-10">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="loader-bar bg-green-700 rounded-md"
            style={{
              width: `${6 + i * 2}px`,
              height: `${35 + i * 15}px`,
              transformOrigin: "bottom center",
            }}
          />
        ))}
      </div>

      {/* Logo */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{
          opacity: [0, 1, 1, 0.9, 1],
          y: 0,
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 3,
          ease: "easeInOut",
          repeat: Infinity,
          repeatDelay: 1,
        }}
        className="text-3xl sm:text-4xl md:text-5xl font-bold text-[#0d2544]"
      >
        Outbreak<span className="text-green-700">IQ</span>
      </motion.div>
    </div>
  );
};

export default Loader;
