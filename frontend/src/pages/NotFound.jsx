import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4 animate-fadeIn space-y-5">
      <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
        <AlertTriangle size={32} />
      </div>
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-white">404 — Page Not Found</h1>
        <p className="text-sm text-gray-400 max-w-md">
          The requested page route does not exist in the Multilingual AI Document Assistant application shell.
        </p>
      </div>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm transition shadow-lg shadow-brand-600/30"
      >
        <Home size={18} />
        <span>Return to Dashboard</span>
      </Link>
    </div>
  );
}
