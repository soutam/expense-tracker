import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useLocation, useNavigate, Navigate } from "react-router-dom";
import axios from "axios";

import { authApi } from "../api/authApi";
import { useAuthStore } from "../store/authStore";
import {
  registerStep2Schema,
  type RegisterStep1Values,
  type RegisterStep2Values,
} from "../types/auth";

const CURRENCIES = [
  { code: "USD", label: "US Dollar (USD)" },
  { code: "EUR", label: "Euro (EUR)" },
  { code: "GBP", label: "British Pound (GBP)" },
  { code: "CAD", label: "Canadian Dollar (CAD)" },
  { code: "AUD", label: "Australian Dollar (AUD)" },
  { code: "INR", label: "Indian Rupee (INR)" },
];

export default function RegisterStep2Page() {
  const navigate = useNavigate();
  const location = useLocation();
  const step1Data = location.state as RegisterStep1Values | null;
  const setUser = useAuthStore((s) => s.setUser);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterStep2Values>({ resolver: zodResolver(registerStep2Schema) });

  if (!step1Data) {
    return <Navigate to="/register" replace />;
  }

  const onSubmit = async (step2Data: RegisterStep2Values) => {
    setApiError(null);
    try {
      // Convert empty strings to null so Pydantic EmailStr validation passes
      const cleanedStep2 = {
        ...step2Data,
        partner_email: step2Data.partner_email || null,
        member2_display_name: step2Data.member2_display_name || null,
      };
      const { data: user } = await authApi.register(step1Data, cleanedStep2);
      setUser(user);
      navigate("/dashboard");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setApiError("This email is already registered. Please sign in instead.");
      } else if (axios.isAxiosError(err) && err.response?.data?.detail) {
        const detail = err.response.data.detail;
        // FastAPI validation errors return detail as an array of objects
        setApiError(
          Array.isArray(detail)
            ? detail.map((e: { msg: string }) => e.msg).join(", ")
            : String(detail)
        );
      } else {
        setApiError("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-md p-8 space-y-6">
        <div>
          <div className="flex items-center justify-between mb-1">
            <h1 className="text-2xl font-bold text-gray-900">Set up your household</h1>
            <span className="text-xs text-gray-400">Step 2 of 2</span>
          </div>
          <p className="text-sm text-gray-500">Configure your household details</p>
        </div>

        {apiError && (
          <div
            role="alert"
            className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700"
          >
            {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label htmlFor="member1_display_name" className="block text-sm font-medium text-gray-700 mb-1">
              Your display name
            </label>
            <input
              id="member1_display_name"
              type="text"
              placeholder={`${step1Data.first_name} ${step1Data.last_name}`}
              {...register("member1_display_name")}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.member1_display_name && (
              <p className="mt-1 text-xs text-red-600">{errors.member1_display_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="member2_display_name" className="block text-sm font-medium text-gray-700 mb-1">
              Partner's display name{" "}
              <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              id="member2_display_name"
              type="text"
              {...register("member2_display_name")}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label htmlFor="partner_email" className="block text-sm font-medium text-gray-700 mb-1">
              Partner's email{" "}
              <span className="text-gray-400 font-normal">(optional — invite later)</span>
            </label>
            <input
              id="partner_email"
              type="email"
              {...register("partner_email")}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {errors.partner_email && (
              <p className="mt-1 text-xs text-red-600">{errors.partner_email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-1">
              Currency
            </label>
            <select
              id="currency"
              {...register("currency")}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
            >
              <option value="">Select a currency…</option>
              {CURRENCIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.label}
                </option>
              ))}
            </select>
            {errors.currency && (
              <p className="mt-1 text-xs text-red-600">{errors.currency.message}</p>
            )}
          </div>

          <p className="text-xs text-gray-500">
            12 default expense categories will be set up automatically.
          </p>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate("/register")}
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-colors"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? "Creating account…" : "Create account"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
