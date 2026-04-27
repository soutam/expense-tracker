import type {
  AuthUser,
  LoginFormValues,
  RegisterStep1Values,
  RegisterStep2Values,
} from "../types/auth";
import axiosClient from "./axiosClient";

export const authApi = {
  login: (data: LoginFormValues) =>
    axiosClient.post<AuthUser>("/auth/login", data),

  register: (step1: RegisterStep1Values, step2: RegisterStep2Values) =>
    axiosClient.post<AuthUser>("/auth/register", { step1, step2 }),

  logout: () => axiosClient.post<void>("/auth/logout"),

  me: () => axiosClient.get<AuthUser>("/auth/me"),

  refresh: () => axiosClient.post<AuthUser>("/auth/refresh"),
};
