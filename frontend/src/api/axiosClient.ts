import axios from "axios";

const axiosClient = axios.create({
  baseURL: "/",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// On 401, clear auth state and redirect to login.
// Import is lazy to avoid circular dependency with authStore.
axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const { useAuthStore } = await import("../store/authStore");
      useAuthStore.getState().clearUser();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;
