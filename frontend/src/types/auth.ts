import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export const registerStep1Schema = z
  .object({
    first_name: z.string().min(1, "First name is required").max(50),
    last_name: z.string().min(1, "Last name is required").max(50),
    email: z.string().email("Enter a valid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export const registerStep2Schema = z.object({
  member1_display_name: z
    .string()
    .min(1, "Display name is required")
    .max(100),
  member2_display_name: z.string().max(100).optional(),
  partner_email: z
    .string()
    .email("Enter a valid email address")
    .optional()
    .or(z.literal("")),
  currency: z.string().length(3, "Select a currency"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterStep1Values = z.infer<typeof registerStep1Schema>;
export type RegisterStep2Values = z.infer<typeof registerStep2Schema>;

export interface AuthUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}
