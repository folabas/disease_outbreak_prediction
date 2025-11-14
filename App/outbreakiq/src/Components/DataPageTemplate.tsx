import { ReactNode } from "react";

interface DataPageTemplateProps {
  title: string;
  description?: string;
  filters?: ReactNode;
  children: ReactNode;
}

const DataPageTemplate = ({
  title,
  description,
  filters,
  children,
}: DataPageTemplateProps) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
          {description && (
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          )}
        </div>
      </div>

      {/* Filters Section */}
      {filters && (
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col space-y-3 sm:flex-row sm:space-y-0 sm:space-x-4">
            {filters}
          </div>
        </div>
      )}

      {/* Content Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Sidebar Filters (Desktop) */}
          <div className="hidden lg:block lg:col-span-1">
            <div className="bg-white shadow rounded-lg p-6 sticky top-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Filters
              </h2>
              {/* Add filter controls here */}
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-2">{children}</div>
        </div>
      </div>
    </div>
  );
};

export default DataPageTemplate;
