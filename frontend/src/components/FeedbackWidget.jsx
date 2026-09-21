import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Check, Send } from 'lucide-react';
import { apiService } from '../services/api';

export default function FeedbackWidget({ queryId }) {
  const [submitted, setSubmitted] = useState(null); // 1 or -1 or null
  const [loading, setLoading] = useState(false);
  const [showCommentBox, setShowCommentBox] = useState(false);
  const [comment, setComment] = useState('');

  if (!queryId) return null;

  async function handleFeedbackClick(score) {
    if (submitted !== null || loading) return;
    setSubmitted(score);
    setShowCommentBox(true);

    try {
      await apiService.submitFeedback(queryId, score, null);
    } catch (err) {
      // Non-blocking telemetry feedback
    }
  }

  async function handleCommentSubmit() {
    if (!comment.trim()) {
      setShowCommentBox(false);
      return;
    }

    setLoading(true);
    try {
      await apiService.submitFeedback(queryId, submitted, comment.trim());
      setShowCommentBox(false);
    } catch (err) {
      setShowCommentBox(false);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="pt-2 text-xs space-y-2">
      {submitted === null ? (
        <div className="flex items-center gap-2 text-gray-400">
          <span className="text-[11px]">Was this answer helpful?</span>
          <button
            onClick={() => handleFeedbackClick(1)}
            className="flex items-center gap-1 px-2 py-1 rounded-lg bg-surface-base hover:bg-surface-card border border-surface-border text-gray-300 hover:text-emerald-400 transition text-[11px]"
            title="Helpful"
          >
            <ThumbsUp size={12} />
            <span>Helpful</span>
          </button>
          <button
            onClick={() => handleFeedbackClick(-1)}
            className="flex items-center gap-1 px-2 py-1 rounded-lg bg-surface-base hover:bg-surface-card border border-surface-border text-gray-300 hover:text-rose-400 transition text-[11px]"
            title="Not Helpful"
          >
            <ThumbsDown size={12} />
            <span>Not Helpful</span>
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-emerald-400 text-[11px] font-medium">
            <Check size={12} />
            <span>Thank you for your feedback!</span>
          </div>

          {showCommentBox && (
            <div className="flex items-center gap-2 max-w-sm pt-1 animate-fadeIn">
              <input
                type="text"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Optional: What could be improved?"
                className="flex-1 px-2.5 py-1 text-xs rounded-lg bg-surface-base border border-surface-border text-white focus:outline-none focus:border-brand-500"
              />
              <button
                onClick={handleCommentSubmit}
                disabled={loading}
                className="p-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs transition"
              >
                <Send size={12} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
