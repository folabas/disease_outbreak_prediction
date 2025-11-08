import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface FAQItem {
  question: string;
  answer: string;
}

const faqs: FAQItem[] = [
  {
    question: "What is OutbreakIQ?",
    answer:
      "OutbreakIQ is an advanced disease outbreak prediction system that uses AI and data analytics to forecast malaria and cholera risks in Nigeria. It helps public health officials make informed decisions for disease prevention and control.",
  },
  {
    question: "How accurate are the predictions?",
    answer:
      "Our system analyzes over 10 years of historical data using advanced AI models, providing high-accuracy predictions. The system continuously learns and improves from new data inputs and validation against actual outbreak occurrences.",
  },
  {
    question: "What data sources do you use?",
    answer:
      "We integrate multiple data sources including climate data, population demographics, hospital records, and historical disease outbreak information to make comprehensive predictions.",
  },
  {
    question: "How can health officials use this platform?",
    answer:
      "Health officials can access the interactive dashboard to view predictions, analyze risk factors, and make data-driven decisions for resource allocation and preventive measures against disease outbreaks.",
  },
  {
    question: "How often are predictions updated?",
    answer:
      "The system regularly updates predictions based on new data inputs, ensuring that health officials have access to the most current risk assessments and forecasts.",
  },
  {
    question: "What diseases does OutbreakIQ track?",
    answer:
      "Currently, OutbreakIQ focuses on predicting malaria and cholera outbreaks in Nigeria, with plans to expand to other infectious diseases in the future.",
  },
];

const FAQ = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="px-4 sm:px-10 md:px-20 lg:px-40 flex justify-center py-24 bg-[#0d2544]">
      <div className="layout-content-container flex flex-col w-full max-w-6xl flex-1">
        <div className="text-center mb-10">
          <h2 className="text-xl font-bold text-gray-300 sm:text-2xl">
            Frequently Asked Questions
          </h2>
          <p className="text-[#6C757D] text-lg">
            Find answers to common questions about OutbreakIQ
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-lg bg-white overflow-hidden"
            >
              <button
                className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-50"
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
              >
                <span className="text-green-700 font-medium">
                  {faq.question}
                </span>
                <span className="material-symbols-outlined text-[#6C757D] text-xl">
                  {openIndex === index ? "-" : "+"}
                </span>
              </button>

              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="px-6 py-4 text-white bg-green-700 border-t">
                      {faq.answer}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FAQ;
