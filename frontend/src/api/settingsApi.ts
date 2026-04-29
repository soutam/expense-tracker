import type {
  CategoryInUseResponse,
  CategoryOut,
  HouseholdOut,
  MemberNamesValues,
} from "../types/settings";
import axiosClient from "./axiosClient";

export const settingsApi = {
  getHousehold: () => axiosClient.get<HouseholdOut>("/settings/household"),

  updateMemberNames: (data: MemberNamesValues) =>
    axiosClient.put<HouseholdOut>("/settings/household/members", data),

  listCategories: () => axiosClient.get<CategoryOut[]>("/settings/categories"),

  createCategory: (name: string) =>
    axiosClient.post<CategoryOut>("/settings/categories", { name }),

  renameCategory: (id: string, name: string) =>
    axiosClient.put<CategoryOut>(`/settings/categories/${id}`, { name }),

  checkCategoryInUse: (id: string) =>
    axiosClient.get<CategoryInUseResponse>(`/settings/categories/${id}/in-use`),

  deleteCategory: (id: string) =>
    axiosClient.delete<void>(`/settings/categories/${id}`),
};
