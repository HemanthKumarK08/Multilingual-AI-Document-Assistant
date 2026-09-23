import React from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

/**
 * Standard React Error Boundary
 * Catches unhandled runtime exceptions in any child component tree
 * and displays a graceful fallback UI instead of crashing to a blank screen.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("[ErrorBoundary caught error]:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 rounded-3xl bg-surface-card border border-rose-500/30 text-rose-300 max-w-xl mx-auto my-8 shadow-2xl space-y-4">
          <div className="flex items-center gap-3 text-rose-400">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20">
              <AlertTriangle size={24} />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Something went wrong</h2>
              <p className="text-xs text-rose-300/80">An unexpected interface error occurred.</p>
            </div>
          </div>

          <p className="text-xs text-gray-300 bg-surface-base/80 p-3 rounded-xl border border-surface-border font-mono break-all">
            {this.state.error?.message || "Unknown runtime error"}
          </p>

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={this.handleReset}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition shadow-md shadow-brand-600/30"
            >
              <RotateCcw size={14} />
              <span>Try Again</span>
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-xl bg-surface-base hover:bg-surface-card border border-surface-border text-gray-300 hover:text-white text-xs font-semibold transition"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
