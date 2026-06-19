import React from 'react';
import { Link } from 'react-router-dom';
import { FiArrowLeft as _FiArrowLeft } from 'react-icons/fi';
const FiArrowLeft = _FiArrowLeft as any;
import FAQComponent from '../Components/FAQ';

const PageWrapper = ({ title, children }: { title: string, children: React.ReactNode }) => (
  <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8 bg-white shadow-sm rounded-2xl mt-8 relative">
    <Link to="/" className="inline-flex items-center text-gray-500 hover:text-green-600 font-medium mb-8 transition-colors">
      <FiArrowLeft className="mr-2" /> Back to Home
    </Link>
    <h1 className="text-3xl font-black text-[#0d2544] mb-6">{title}</h1>
    <div className="prose prose-green max-w-none text-gray-600">
      {children}
    </div>
  </div>
);

export const About = () => (
  <PageWrapper title="About Us">
    <p>OutbreakIQ is dedicated to predicting and mitigating disease outbreaks across Nigeria using advanced AI and data analytics.</p>
    <p>Our mission is to provide public health officials with the insights they need to act proactively and save lives.</p>
  </PageWrapper>
);

export const Team = () => (
  <PageWrapper title="Our Team">
    <p>We are a multidisciplinary team of data scientists, epidemiologists, and software engineers passionate about public health.</p>
  </PageWrapper>
);

export const Documentation = () => (
  <PageWrapper title="Documentation">
    <p>Welcome to the OutbreakIQ Documentation. Here you will find guides on how to use the dashboard, interpret the predictive models, and integrate our data.</p>
    <p><em>Documentation content coming soon.</em></p>
  </PageWrapper>
);

export const ApiPage = () => (
  <PageWrapper title="API Reference">
    <p>Integrate OutbreakIQ predictions directly into your own health systems.</p>
    <p><em>API endpoints and authentication details coming soon.</em></p>
  </PageWrapper>
);

export const Contact = () => (
  <PageWrapper title="Contact Us">
    <p>Have questions or want to partner with us? Reach out at <strong>support@outbreakiq.ng</strong>.</p>
  </PageWrapper>
);

export const FaqPage = () => (
  <div className="mt-8">
    <FAQComponent />
  </div>
);

export const Privacy = () => (
  <PageWrapper title="Privacy Policy">
    <p>Your privacy is important to us. This policy outlines how we collect, use, and protect your data.</p>
    <p><em>Full privacy policy text coming soon.</em></p>
  </PageWrapper>
);

export const Terms = () => (
  <PageWrapper title="Terms of Service">
    <p>By using OutbreakIQ, you agree to these terms. Our platform is intended for informational and preparatory use by health professionals.</p>
    <p><em>Full terms of service text coming soon.</em></p>
  </PageWrapper>
);
