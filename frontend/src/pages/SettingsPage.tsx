import axios from "axios";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";

import { settingsApi } from "../api/settingsApi";
import { useSettingsStore } from "../store/settingsStore";
import {
  categoryCreateSchema,
  memberNamesSchema,
  type CategoryCreateValues,
  type MemberNamesValues,
} from "../types/settings";
import type { CategoryOut } from "../types/settings";

// ---------------------------------------------------------------------------
// Member Names Section
// ---------------------------------------------------------------------------

function MemberNamesSection() {
  const household = useSettingsStore((s) => s.household);
  const setHousehold = useSettingsStore((s) => s.setHousehold);
  const [success, setSuccess] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<MemberNamesValues>({
    resolver: zodResolver(memberNamesSchema),
  });

  useEffect(() => {
    if (household) {
      reset({
        member1_name: household.member1_name,
        member2_name: household.member2_name ?? "",
      });
    }
  }, [household, reset]);

  const onSubmit = async (values: MemberNamesValues) => {
    setApiError(null);
    setSuccess(false);
    try {
      const { data } = await settingsApi.updateMemberNames({
        member1_name: values.member1_name,
        member2_name: values.member2_name || undefined,
      });
      setHousehold(data);
      setSuccess(true);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setApiError(String(err.response.data.detail));
      } else {
        setApiError("Failed to save. Please try again.");
      }
    }
  };

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-base font-semibold text-gray-900 mb-4">Household member names</h2>

      {success && (
        <div role="status" className="mb-4 rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700">
          Member names updated successfully.
        </div>
      )}
      {apiError && (
        <div role="alert" className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <div>
          <label htmlFor="member1_name" className="block text-sm font-medium text-gray-700 mb-1">
            Member 1 name
          </label>
          <input
            id="member1_name"
            type="text"
            {...register("member1_name")}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {errors.member1_name && (
            <p className="mt-1 text-xs text-red-600">{errors.member1_name.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="member2_name" className="block text-sm font-medium text-gray-700 mb-1">
            Member 2 name{" "}
            <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            id="member2_name"
            type="text"
            {...register("member2_name")}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {errors.member2_name && (
            <p className="mt-1 text-xs text-red-600">{errors.member2_name.message}</p>
          )}
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? "Saving…" : "Save names"}
          </button>
        </div>
      </form>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Delete Confirmation Modal
// ---------------------------------------------------------------------------

interface DeleteModalProps {
  categoryName: string;
  transactionCount: number;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}

function DeleteConfirmModal({ categoryName, transactionCount, onConfirm, onCancel, isDeleting }: DeleteModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-lg p-6 space-y-4">
        <h3 className="text-base font-semibold text-gray-900">Delete &ldquo;{categoryName}&rdquo;?</h3>
        {transactionCount > 0 ? (
          <p className="text-sm text-gray-600">
            This category is used by{" "}
            <span className="font-medium text-red-600">{transactionCount} transaction{transactionCount !== 1 ? "s" : ""}</span>.
            Deleting it will remove the category from those transactions.
          </p>
        ) : (
          <p className="text-sm text-gray-600">This category has no transactions. Are you sure you want to delete it?</p>
        )}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="flex-1 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
          >
            {isDeleting ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Category Row
// ---------------------------------------------------------------------------

interface CategoryRowProps {
  category: CategoryOut;
  onRenamed: (id: string, newName: string) => void;
  onDeleted: (id: string) => void;
}

function CategoryRow({ category, onRenamed, onDeleted }: CategoryRowProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(category.name);
  const [editError, setEditError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const [deleteModal, setDeleteModal] = useState<{ transactionCount: number } | null>(null);
  const [isCheckingUse, setIsCheckingUse] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleEditStart = () => {
    setEditValue(category.name);
    setEditError(null);
    setIsEditing(true);
  };

  const handleEditCancel = () => {
    setIsEditing(false);
    setEditError(null);
  };

  const handleEditSave = async () => {
    const trimmed = editValue.trim();
    if (!trimmed) {
      setEditError("Name cannot be empty");
      return;
    }
    setIsSaving(true);
    setEditError(null);
    try {
      const { data } = await settingsApi.renameCategory(category.id, trimmed);
      onRenamed(category.id, data.name);
      setIsEditing(false);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setEditError("A category with this name already exists");
      } else if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setEditError(String(err.response.data.detail));
      } else {
        setEditError("Failed to rename. Please try again.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteClick = async () => {
    setIsCheckingUse(true);
    try {
      const { data } = await settingsApi.checkCategoryInUse(category.id);
      setDeleteModal({ transactionCount: data.transaction_count });
    } catch {
      setDeleteModal({ transactionCount: 0 });
    } finally {
      setIsCheckingUse(false);
    }
  };

  const handleDeleteConfirm = async () => {
    setIsDeleting(true);
    try {
      await settingsApi.deleteCategory(category.id);
      onDeleted(category.id);
    } catch {
      setDeleteModal(null);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      {deleteModal && (
        <DeleteConfirmModal
          categoryName={category.name}
          transactionCount={deleteModal.transactionCount}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeleteModal(null)}
          isDeleting={isDeleting}
        />
      )}

      <li className="flex items-center gap-3 py-2.5 border-b border-gray-100 last:border-0">
        {isEditing ? (
          <div className="flex-1 flex items-center gap-2">
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleEditSave();
                if (e.key === "Escape") handleEditCancel();
              }}
              autoFocus
              className="flex-1 rounded-lg border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {editError && <span className="text-xs text-red-600 shrink-0">{editError}</span>}
            <button
              onClick={handleEditSave}
              disabled={isSaving}
              className="rounded px-2 py-1 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSaving ? "…" : "Save"}
            </button>
            <button
              onClick={handleEditCancel}
              className="rounded px-2 py-1 text-xs font-medium text-gray-600 border border-gray-300 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        ) : (
          <>
            <span className="flex-1 text-sm text-gray-800">{category.name}</span>
            {category.is_default && (
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500 font-medium">
                Default
              </span>
            )}
            <button
              onClick={handleEditStart}
              title="Rename"
              className="p-1 rounded text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
            </button>
            {!category.is_default && (
              <button
                onClick={handleDeleteClick}
                disabled={isCheckingUse}
                title="Delete"
                className="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
              >
                {isCheckingUse ? (
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            )}
          </>
        )}
      </li>
    </>
  );
}

// ---------------------------------------------------------------------------
// Categories Section
// ---------------------------------------------------------------------------

function CategoriesSection() {
  const categories = useSettingsStore((s) => s.categories);
  const setCategories = useSettingsStore((s) => s.setCategories);
  const [addError, setAddError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CategoryCreateValues>({
    resolver: zodResolver(categoryCreateSchema),
  });

  const handleAdd = async (values: CategoryCreateValues) => {
    setAddError(null);
    try {
      const { data } = await settingsApi.createCategory(values.name);
      setCategories([...categories, data]);
      reset();
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setAddError("A category with this name already exists");
      } else if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setAddError(String(err.response.data.detail));
      } else {
        setAddError("Failed to add category. Please try again.");
      }
    }
  };

  const handleRenamed = (id: string, newName: string) => {
    setCategories(categories.map((c) => (c.id === id ? { ...c, name: newName } : c)));
  };

  const handleDeleted = (id: string) => {
    setCategories(categories.filter((c) => c.id !== id));
  };

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-base font-semibold text-gray-900 mb-4">Expense categories</h2>

      <form onSubmit={handleSubmit(handleAdd)} noValidate className="flex gap-2 mb-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="New category name…"
            {...register("name")}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
          )}
          {addError && (
            <p className="mt-1 text-xs text-red-600">{addError}</p>
          )}
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="shrink-0 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? "Adding…" : "Add"}
        </button>
      </form>

      {categories.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-4">No categories yet.</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {categories.map((category) => (
            <CategoryRow
              key={category.id}
              category={category}
              onRenamed={handleRenamed}
              onDeleted={handleDeleted}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Settings Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const fetchHousehold = useSettingsStore((s) => s.fetchHousehold);
  const fetchCategories = useSettingsStore((s) => s.fetchCategories);
  const isLoading = useSettingsStore((s) => s.isLoading);

  useEffect(() => {
    fetchHousehold();
    fetchCategories();
  }, [fetchHousehold, fetchCategories]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-900">Settings</h1>
          <Link
            to="/dashboard"
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            ← Dashboard
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-8 space-y-6">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <svg className="h-8 w-8 animate-spin text-indigo-600" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
        ) : (
          <>
            <MemberNamesSection />
            <CategoriesSection />
          </>
        )}
      </main>
    </div>
  );
}
