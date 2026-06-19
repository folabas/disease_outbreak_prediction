import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';

interface ScrollStackProps {
  children: React.ReactNode[];
  desktopClasses?: string;
  childClasses?: string;
}

const ScrollStack = ({ children, desktopClasses = '', childClasses = '' }: ScrollStackProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const scrollPosition = scrollRef.current.scrollLeft;
    const itemElement = scrollRef.current.firstElementChild as HTMLElement;
    if (!itemElement) return;
    
    // Calculate index based on scroll position
    const itemWidth = itemElement.clientWidth; 
    const newIndex = Math.round(scrollPosition / itemWidth);
    
    if (newIndex !== activeIndex && newIndex >= 0 && newIndex < children.length) {
      setActiveIndex(newIndex);
    }
  };

  const scrollTo = (index: number) => {
    if (!scrollRef.current) return;
    const itemElement = scrollRef.current.firstElementChild as HTMLElement;
    if (!itemElement) return;
    
    const itemWidth = itemElement.clientWidth;
    scrollRef.current.scrollTo({
      left: itemWidth * index,
      behavior: 'smooth',
    });
    setActiveIndex(index);
  };

  return (
    <div className="relative w-full">
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className={`flex overflow-x-auto snap-x snap-mandatory hide-scrollbar pb-4 -mx-4 px-4 ${desktopClasses}`}
      >
        {children.map((child, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className={`w-[85vw] flex-shrink-0 snap-center pr-4 ${childClasses}`}
          >
            {child}
          </motion.div>
        ))}
      </div>

      {/* Pagination Dots (Mobile Only) */}
      <div className="flex justify-center space-x-2 mt-4 mb-2 md:hidden">
        {children.map((_, index) => (
          <button
            key={index}
            onClick={() => scrollTo(index)}
            className={`h-2 rounded-full transition-all duration-300 ${
              activeIndex === index ? 'bg-green-600 w-6' : 'bg-gray-300 w-2 hover:bg-green-400'
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default ScrollStack;
