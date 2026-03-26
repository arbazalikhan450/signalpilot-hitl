import { useEffect, useState } from "react";

type Platform = "LINKEDIN" | "X";
type PostStatus =
  | "DRAFT_CREATED"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "SCHEDULED"
  | "POSTED";

type Post = {
  id: string;
  user_id: string;
  topic: string;
  tone: string;
  platform: Platform;
  content: string;
  status: PostStatus;
  scheduled_for: string | null;
  posted_at: string | null;
  created_at: string;
  updated_at: string;
};

const API_BASE = "http://localhost:8000/api/v1";
const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";
const REVIEWER_ID = DEMO_USER_ID;

const emptyForm = {
  topic: "",
  tone: "professional",
  platform: "LINKEDIN" as Platform,
  schedule_for: "",
};

export default function App() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [draftEdits, setDraftEdits] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function fetchPosts() {
      const response = await fetch(`${API_BASE}/posts`);
    if (!response.ok) {
      throw new Error("Failed to fetch posts.");
    }
    const data = await response.json();
    setPosts(data.items);
  }

  useEffect(() => {
    fetchPosts().catch((err: Error) => setError(err.message));
  }, []);

  async function generatePost(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/generate-post`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: DEMO_USER_ID,
          topic: form.topic,
          tone: form.tone,
          platform: form.platform,
          schedule_for: form.schedule_for || null,
        }),
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail ?? "Unable to generate post.");
      }
      setForm(emptyForm);
      await fetchPosts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function approvePost(post: Post) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_id: post.id,
          reviewer_id: REVIEWER_ID,
          notes: notes[post.id] || null,
          edited_content: draftEdits[post.id] || post.content,
          schedule_for: post.scheduled_for,
        }),
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail ?? "Unable to approve post.");
      }
      await fetchPosts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function rejectPost(postId: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_id: postId,
          reviewer_id: REVIEWER_ID,
          notes: notes[postId] || null,
        }),
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail ?? "Unable to reject post.");
      }
      await fetchPosts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function publishPost(postId: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ post_id: postId }),
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail ?? "Unable to queue publish.");
      }
      await fetchPosts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">SignalPilot</p>
          <h1>Human approval before every publish.</h1>
          <p className="hero-copy">
            Generate platform-aware drafts, review them in queue, edit before approval,
            and hand off approved content to the async publishing pipeline.
          </p>
        </div>
        <div className="hero-panel">
          <span>Workflow</span>
          <strong>DRAFT → APPROVAL → SCHEDULE/PUBLISH → POSTED</strong>
        </div>
      </header>

      <main className="grid">
        <section className="card composer">
          <div className="section-head">
            <h2>Create Draft</h2>
            <span>{loading ? "Working..." : "Ready"}</span>
          </div>
          <form onSubmit={generatePost}>
            <label>
              Topic
              <input
                value={form.topic}
                onChange={(event) => setForm({ ...form, topic: event.target.value })}
                placeholder="Launching our new AI agent workflow"
                required
              />
            </label>
            <label>
              Tone
              <input
                value={form.tone}
                onChange={(event) => setForm({ ...form, tone: event.target.value })}
                placeholder="professional"
                required
              />
            </label>
            <div className="row">
              <label>
                Platform
                <select
                  value={form.platform}
                  onChange={(event) =>
                    setForm({ ...form, platform: event.target.value as Platform })
                  }
                >
                  <option value="LINKEDIN">LinkedIn</option>
                  <option value="X">X</option>
                </select>
              </label>
              <label>
                Schedule
                <input
                  type="datetime-local"
                  value={form.schedule_for}
                  onChange={(event) => setForm({ ...form, schedule_for: event.target.value })}
                />
              </label>
            </div>
            <button type="submit" disabled={loading}>
              Generate Post
            </button>
          </form>
          {error ? <p className="error">{error}</p> : null}
        </section>

        <section className="card queue">
          <div className="section-head">
            <h2>Approval Queue</h2>
            <button className="ghost" onClick={() => fetchPosts().catch(() => undefined)}>
              Refresh
            </button>
          </div>

          <div className="post-list">
            {posts.map((post) => (
              <article className="post-card" key={post.id}>
                <div className="post-meta">
                  <span>{post.platform}</span>
                  <span className={`status status-${post.status.toLowerCase()}`}>{post.status}</span>
                </div>
                <h3>{post.topic}</h3>
                <p className="post-subtitle">
                  Tone: {post.tone} | Created: {new Date(post.created_at).toLocaleString()}
                </p>
                <textarea
                  value={draftEdits[post.id] ?? post.content}
                  onChange={(event) =>
                    setDraftEdits((current) => ({ ...current, [post.id]: event.target.value }))
                  }
                  rows={6}
                />
                <textarea
                  value={notes[post.id] ?? ""}
                  onChange={(event) =>
                    setNotes((current) => ({ ...current, [post.id]: event.target.value }))
                  }
                  rows={3}
                  placeholder="Reviewer notes"
                />
                <div className="actions">
                  <button onClick={() => approvePost(post)} disabled={loading}>
                    Approve
                  </button>
                  <button className="danger" onClick={() => rejectPost(post.id)} disabled={loading}>
                    Reject
                  </button>
                  <button className="ghost" onClick={() => publishPost(post.id)} disabled={loading}>
                    Publish Now
                  </button>
                </div>
              </article>
            ))}
            {posts.length === 0 ? <p className="empty">No drafts yet. Generate the first one.</p> : null}
          </div>
        </section>
      </main>
    </div>
  );
}
