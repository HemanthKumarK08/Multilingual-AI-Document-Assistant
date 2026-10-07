import React, { useEffect, useState } from 'react';
import { Menu, X, Sparkles, Globe } from 'lucide-react';
import { apiService } from '../services/api';

export default function Header({ isSidebarOpen, setIsSidebarOpen }) {
  const [isOnline, setIsOnline] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function checkStatus() {
      try {
        const res = await apiService.getHealth();
        if (isMounted) setIsOnline(res.status === 'ok');
      } catch (err) {
        if (isMounted) setIsOnline(false);
      }
    }
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 h-16 bg-surface-base/80 backdrop-blur-md border-b border-surface-border px-4 lg:px-8 flex items-center justify-between">
      {/* Left: Mobile Toggle & Project Branding */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          aria-label="Toggle Navigation Menu"
          className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-card lg:hidden focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-brand-500/20">
            <Sparkles size={18} />
          </div>
          <div>
            <h1 className="text-sm sm:text-base font-bold text-white tracking-tight leading-tight flex items-center gap-2">
              Multilingual AI Document Assistant
            </h1>
            <p className="text-[11px] text-gray-400 hidden sm:block">
              AI-Powered Document Intelligence & Big Data Analytics
            </p>
          </div>
        </div>
      </div>

      {/* Right: Status Pill & Language Indicator */}
      <div className="flex items-center gap-3">
        {/* Backend Live Indicator */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-surface-card border border-surface-border text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              isOnline === true
                ? 'bg-emerald-400 shadow-sm shadow-emerald-400'
                : isOnline === false
                ? 'bg-rose-500 shadow-sm shadow-rose-500'
                : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span className="text-gray-300 font-medium hidden xs:inline">
            {isOnline === true ? 'Backend Online' : isOnline === false ? 'Offline' : 'Connecting...'}
          </span>
        </div>

        {/* Language Capability Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-xs text-brand-300">
          <Globe size={13} />
          <span>EN • HI • KN • TE</span>
        </div>
      </div>
    </header>
  );
}
