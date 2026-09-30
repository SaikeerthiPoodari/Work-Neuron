import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get, post } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";

export default function ReviewsPage() {
  const { user } = useAuth();
  const [assignments, setAssignments] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [form, setForm] = useState({ assignment: "", rating: 5, review: "" });
  const [error, setError] = useState("");
  const load = async () => {
    try {
      const [allAssignments, allReviews] = await Promise.all([get("/assignments/"), get("/reviews/")]);
      setAssignments(allAssignments.filter((item) => item.task_status === "COMPLETED"));
      setReviews(allReviews);
    } catch (err) { setError(err.message); }
  };
  useEffect(() => { load(); }, []);
  const submit = async (event) => {
    event.preventDefault();
    try {
      await post("/reviews/", { ...form, assignment: Number(form.assignment), rating: Number(form.rating) });
      setForm({ assignment: "", rating: 5, review: "" });
      await load();
    } catch (err) { setError(err.message); }
  };

  return <div className="space-y-6">
    <div><p className="text-sm font-semibold text-brand">Trust layer</p><h1 className="mt-1 text-3xl font-black">Reviews</h1><p className="mt-2 text-slate-500">Ratings and comments linked to completed WorkNeuron assignments.</p></div>
    <ErrorMessage message={error} />
    {assignments.length > 0 && <form onSubmit={submit} className="card grid gap-4 md:grid-cols-3"><select required className="field mt-0" value={form.assignment} onChange={(event) => setForm({ ...form, assignment: event.target.value })}><option value="">Completed assignment</option>{assignments.map((item) => <option value={item.id} key={item.id}>{item.task_title}</option>)}</select><select className="field mt-0" value={form.rating} onChange={(event) => setForm({ ...form, rating: event.target.value })}>{[5, 4, 3, 2, 1].map((rating) => <option key={rating} value={rating}>{rating} stars</option>)}</select><input required className="field mt-0" placeholder="Share a useful review" value={form.review} onChange={(event) => setForm({ ...form, review: event.target.value })} /><button className="button-primary md:col-span-3">Submit review</button></form>}
    {reviews.length ? <div className="space-y-3">{reviews.map((review) => <article className="card" key={review.id}><div className="flex flex-wrap justify-between gap-2"><div><h2 className="font-bold">{review.assignment_title}</h2><p className="mt-1 text-sm text-slate-500">From {user.role === "WORKER" ? "client" : "worker"} {review.reviewer_email}</p></div><div className="text-right"><span className="font-bold text-amber-600">{review.rating}/5 ★</span><p className="mt-1 text-xs text-slate-400">{new Date(review.created_at).toLocaleDateString()}</p></div></div><p className="mt-3 text-sm leading-6 text-slate-600">{review.review || "No written comment."}</p></article>)}</div> : <EmptyState>No reviews yet.</EmptyState>}
  </div>;
}
