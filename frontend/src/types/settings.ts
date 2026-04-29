import { z } from "zod";

export const memberNamesSchema = z.object({
  member1_name: z.string().min(1, "Member 1 name is required").max(100),
  member2_name: z.string().max(100).optional(),
});

export const categoryCreateSchema = z.object({
  name: z.string().min(1, "Category name is required").max(100),
});

export const categoryRenameSchema = z.object({
  name: z.string().min(1, "Category name is required").max(100),
});

export type MemberNamesValues = z.infer<typeof memberNamesSchema>;
export type CategoryCreateValues = z.infer<typeof categoryCreateSchema>;
export type CategoryRenameValues = z.infer<typeof categoryRenameSchema>;

export interface HouseholdOut {
  id: string;
  member1_name: string;
  member2_name: string | null;
  currency: string;
}

export interface CategoryOut {
  id: string;
  name: string;
  is_default: boolean;
}

export interface CategoryInUseResponse {
  in_use: boolean;
  transaction_count: number;
}
