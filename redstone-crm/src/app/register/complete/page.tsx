"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, fetchProfile } from "@/src/lib/api";
import { auth } from "@/src/lib/firebase";
import { onAuthStateChanged, signOut } from "firebase/auth";

interface FormData {
  display_name: string;
  username: string;
  phone: string;
  role: string;
  company: string;
  timezone: string;
}

const TIMEZONES = [
  "America/New_York", "America/Chicago", "America/Denver",
  "America/Los_Angeles", "America/Anchorage", "Pacific/Honolulu",
  "Europe/London", "Europe/Berlin", "Asia/Dubai", "Asia/Karachi",
  "Asia/Kolkata", "Asia/Singapore", "Australia/Sydney",
];

const STEPS = [
  { num: 1, label: "Personal Info" },
  { num: 2, label: "Contact" },
  { num: 3, label: "Work Setup" },
  { num: 4, label: "Review" },
];

export default function RegisterCompletePage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [email, setEmail] = useState("");

  const [form, setForm] = useState<FormData>({
    display_name: "",
    username: "",
    phone: "",
    role: "agent",
    company: "",
    timezone: "America/New_York",
  });

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (user) => {
      if (!user || !getToken()) {
        router.replace("/login");
        return;
      }
      setEmail(user.email || "");
      try {
        const profile = await fetchProfile();
        if (profile.registration_complete) {
          router.replace("/dashboard");
          return;
        }
        setForm((prev) => ({
          ...prev,
          display_name: profile.display_name || "",
          username: profile.username || user.email?.split("@")[0] || "",
        }));
      } catch {
        router.replace("/login");
      }
      setLoading(false);
    });
    return () => unsub();
  }, [router]);

  function updateField(field: keyof FormData, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function validateStep(s: number): boolean {
    const errs: string[] = [];
    if (s === 1) {
      if (!form.display_name.trim()) errs.push("Display name is required");
      if (!form.username.trim()) errs.push("Username is required");
      else if (form.username.length < 3) errs.push("Username must be at least 3 characters");
    }
    if (s === 2) {
      if (!form.phone.trim()) errs.push("Phone number is required");
      else if (!/^[\d\s\-\(\)\+]{7,20}$/.test(form.phone.trim()))
        errs.push("Enter a valid phone number");
    }
    setErrors(errs);
    return errs.length === 0;
  }

  function nextStep() {
    if (validateStep(step)) setStep((s) => Math.min(s + 1, 4));
  }

  function prevStep() {
    setStep((s) => Math.max(s - 1, 1));
    setErrors([]);
  }

  async function handleSubmit() {
    if (!validateStep(3)) return;
    setSaving(true);
    setErrors([]);

    try {
      const res = await fetch("/api/auth/complete-registration", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail?.errors?.join(", ") || "Registration failed");
      }
      router.replace("/dashboard");
    } catch (e: unknown) {
      setErrors([e instanceof Error ? e.message : "Something went wrong"]);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-base">
        <p className="text-sm text-text-tertiary">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-base px-4 py-10">
      <div className="w-full max-w-lg">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-signal/15 text-lg font-semibold text-signal">
            R
          </div>
          <h1 className="text-lg font-semibold text-text-primary">Complete Your Registration</h1>
          <p className="mt-1 text-sm text-text-secondary">{email}</p>
        </div>

        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((s) => (
              <div key={s.num} className="flex flex-col items-center gap-1">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium ${
                    s.num < step
                      ? "bg-signal text-base"
                      : s.num === step
                        ? "border-2 border-signal text-signal"
                        : "border border-border-soft text-text-tertiary"
                  }`}
                >
                  {s.num < step ? "✓" : s.num}
                </div>
                <span
                  className={`text-[10px] ${
                    s.num <= step ? "text-text-primary" : "text-text-tertiary"
                  }`}
                >
                  {s.label}
                </span>
              </div>
            ))}
          </div>
          <div className="relative mt-2">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border-soft" />
            </div>
            <div className="relative flex justify-between px-3">
              {[25, 50, 75].map((pct) => (
                <div
                  key={pct}
                  className={`h-2 w-2 rounded-full ${step * 25 >= pct ? "bg-signal" : "bg-border-soft"}`}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border-soft bg-panel p-6">
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-text-primary">Personal Information</h2>
              <p className="text-xs text-text-tertiary">Tell us a bit about yourself.</p>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">
                  Display Name <span className="text-red">*</span>
                </label>
                <input
                  type="text"
                  value={form.display_name}
                  onChange={(e) => updateField("display_name", e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">
                  Username <span className="text-red">*</span>
                </label>
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => updateField("username", e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                  placeholder="johndoe"
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-text-primary">Contact Information</h2>
              <p className="text-xs text-text-tertiary">How can we reach you?</p>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">
                  Phone Number <span className="text-red">*</span>
                </label>
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => updateField("phone", e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                  placeholder="+1 (555) 123-4567"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">Timezone</label>
                <select
                  value={form.timezone}
                  onChange={(e) => updateField("timezone", e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                >
                  {TIMEZONES.map((tz) => (
                    <option key={tz} value={tz}>{tz.replace("_", " ")}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-text-primary">Work Setup</h2>
              <p className="text-xs text-text-tertiary">Configure your workspace.</p>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">Role</label>
                <select
                  value={form.role}
                  onChange={(e) => updateField("role", e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                >
                  <option value="agent">Agent</option>
                  <option value="supervisor">Supervisor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-secondary">Company (optional)</label>
                <input
                  type="text"
                  value={form.company}
                  onChange={(e) => updateField("company", e.target.value)}
                  className="w-full rounded-md border border-border-soft bg-panel-raised px-3 py-2 text-sm text-text-primary outline-none focus:border-signal/50 focus:ring-1 focus:ring-signal/20"
                  placeholder="Your company name"
                />
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-text-primary">Review & Confirm</h2>
              <p className="text-xs text-text-tertiary">Please verify your information before submitting.</p>
              <div className="space-y-3 rounded-md bg-panel-raised p-4">
                <Row label="Email" value={email} />
                <Row label="Display Name" value={form.display_name} />
                <Row label="Username" value={form.username} />
                <Row label="Phone" value={form.phone} />
                <Row label="Timezone" value={form.timezone.replace("_", " ")} />
                <Row label="Role" value={form.role.charAt(0).toUpperCase() + form.role.slice(1)} />
                {form.company && <Row label="Company" value={form.company} />}
              </div>
            </div>
          )}

          {errors.length > 0 && (
            <div className="mt-4 rounded-md border border-red/30 bg-red-dim/10 p-3">
              {errors.map((err, i) => (
                <p key={i} className="text-sm text-red">{err}</p>
              ))}
            </div>
          )}

          <div className="mt-6 flex items-center justify-between">
            <button
              type="button"
              onClick={step === 1 ? () => {
                signOut(auth);
                localStorage.removeItem("token");
                router.replace("/login");
              } : prevStep}
              className="rounded-md border border-border-soft px-4 py-2 text-xs font-medium text-text-secondary transition-colors hover:bg-panel-raised"
            >
              {step === 1 ? "Cancel" : "Back"}
            </button>

            {step < 4 ? (
              <button
                type="button"
                onClick={nextStep}
                className="rounded-md bg-signal px-6 py-2 text-xs font-medium text-base transition-opacity hover:opacity-90"
              >
                Continue
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={saving}
                className="rounded-md bg-signal px-6 py-2 text-xs font-medium text-base transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {saving ? "Submitting..." : "Complete Registration"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border-soft pb-2 last:border-0 last:pb-0">
      <span className="text-xs text-text-tertiary">{label}</span>
      <span className="text-xs font-medium text-text-primary">{value}</span>
    </div>
  );
}
