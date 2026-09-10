import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get, post } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";

export default function PaymentsPage() {
  const { user } = useAuth();
  const [payments, setPayments] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [error, setError] = useState("");
  const load = async () => {
    try {
      const [transactions, allAssignments] = await Promise.all([get("/payments/"), get("/assignments/")]);
      setPayments(transactions);
      setAssignments(allAssignments.filter((item) => item.task_status === "COMPLETED"));
    } catch (e) { setError(e.message); }
  };
  useEffect(() => { load(); }, []);
  const createOrder = async (assignment) => {
    try {
      const data = await post("/payments/create-order/", { assignment: assignment.id });
      if (window.Razorpay && data.order) {
        const checkout = new window.Razorpay({ key: data.key_id, amount: data.order.amount, currency: data.order.currency, name: "WorkNeuron", description: assignment.task_title, order_id: data.order.id, handler: async (response) => {
          try { await post("/payments/verify/", { transaction_id: data.transaction.id, razorpay_order_id: response.razorpay_order_id, razorpay_payment_id: response.razorpay_payment_id, razorpay_signature: response.razorpay_signature }); load(); } catch (e) { setError(e.message); }
        } });
        checkout.open();
      } else { setError("Razorpay checkout is unavailable. The TEST MODE order was created."); load(); }
    } catch (e) { setError(e.message); }
  };
  return <div className="space-y-6"><div><p className="text-sm font-semibold text-brand">Secure checkout</p><h1 className="mt-1 text-3xl font-black">Payments</h1><p className="mt-2 text-slate-500">Razorpay integration is restricted to TEST MODE.</p></div><ErrorMessage message={error} />{user.role === "CLIENT" && assignments.map((assignment) => <div className="card flex flex-col justify-between gap-4 sm:flex-row sm:items-center" key={assignment.id}><div><h2 className="font-bold">{assignment.task_title}</h2><p className="mt-1 text-sm text-slate-500">Payment is available after completion approval.</p></div><button className="button-primary" onClick={() => createOrder(assignment)}>Pay in test mode</button></div>)}{payments.length ? <div className="card"><h2 className="font-bold">Transaction history</h2><div className="mt-4 divide-y divide-slate-100">{payments.map((payment) => <div className="flex justify-between py-3 text-sm" key={payment.id}><span>{payment.assignment_title} · {payment.currency} {payment.amount}</span><span className="font-bold text-brand">{payment.status}</span></div>)}</div></div> : <EmptyState>No transactions yet.</EmptyState>}</div>;
}
