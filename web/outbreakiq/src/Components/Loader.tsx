import React from "react";

const SkeletonCard: React.FC = () => (
  <div className="rounded-lg bg-white shadow p-4 animate-pulse">
    <div className="h-6 bg-slate-200 rounded w-3/4 mb-4" />
    <div className="space-y-2">
      <div className="h-4 bg-slate-200 rounded w-full" />
      <div className="h-4 bg-slate-200 rounded w-5/6" />
      <div className="h-4 bg-slate-200 rounded w-2/3" />
    </div>
  </div>
);

const Loader: React.FC = () => {
  return (
    <div className="min-h-[300px] flex items-center justify-center">
      <div className="grid gap-4 w-full sm:grid-cols-2 lg:grid-cols-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  );
};

export default Loader;
