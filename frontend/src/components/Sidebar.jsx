import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Files,
  BotMessageSquare,
  BarChart3,
  Settings,
  ExternalLink,
  ShieldCheck,
  Building2,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Documents', path: '/documents', icon: Files },
  { name: 'Ask AI', path: '/ask', icon: BotMessageSquare },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export default function Sidebar({ isSidebarOpen, setIsSidebarOpen }) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:sticky top-0 lg:top-16 z-50 lg:z-0 h-screen lg:h-[calc(100vh-4rem)] w-64 bg-surface-sidebar/95 lg:bg-surface-sidebar/50 backdrop-blur-md border-r border-surface-border flex flex-col justify-between transition-transform duration-200 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-4 space-y-6">
          {/* Institution / Project Badge */}
          <div className="px-3 py-2.5 rounded-xl bg-gradient-to-br from-surface-card to-brand-950/40 border border-surface-border flex items-center gap-3">
            <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400">
              <Building2 size={20} />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold tracking-wider text-brand-300">
                Major Project
              </p>
              <p className="text-xs font-semibold text-white">
                Bangalore Inst. of Tech.
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1" aria-label="Main Navigation">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  onClick={() => setIsSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                      isActive
                        ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                        : 'text-gray-400 hover:text-white hover:bg-surface-card'
                    }`
                  }
                >
                  <Icon size={18} />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Footer / System Info */}
        <div className="p-4 border-t border-surface-border space-y-3">
          <div className="px-3 py-2 rounded-lg bg-surface-card/60 border border-surface-border/50 text-[11px] text-gray-400 space-y-1">
            <div className="flex items-center justify-between text-gray-300 font-medium">
              <span className="flex items-center gap-1.5">
                <ShieldCheck size={13} className="text-emerald-400" />
                Zero-Raw-Data Privacy
              </span>
              <span className="text-[10px] text-emerald-400 font-bold">Active</span>
            </div>
            <p className="text-gray-500 text-[10px]">
              PySpark Batch & Hybrid Vector RAG
            </p>
          </div>

          <div className="flex items-center justify-between px-2 text-[11px] text-gray-500">
            <span>FastAPI • ChromaDB • PySpark</span>
            <span>v0.1.0</span>
          </div>
        </div>
      </aside>
    </>
  );
}
