import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { API_BASE_URL } from "./config";

export const api = axios.create({ baseURL: API_BASE_URL, timeout: 15000 });

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ----------------------------- API helpers
export const login = (username, password) =>
  api.post("/api/auth/login/", { username, password }).then((r) => r.data);

export const listSheep = () => api.get("/api/sheep/").then((r) => r.data);

export const getSheepHistory = (tagId) =>
  api.get(`/api/sheep/${tagId}/history/`).then((r) => r.data);

export const verifySheep = (tagId) =>
  api.get(`/api/sheep/${tagId}/verify/`).then((r) => r.data);

export const addEvent = (tagId, payload) =>
  api.post(`/api/sheep/${tagId}/event/`, payload).then((r) => r.data);

export const registerSheep = (payload) =>
  api.post("/api/sheep/", payload).then((r) => r.data);

export const qrCodeUrl = (tagId) =>
  `${API_BASE_URL}/api/sheep/${tagId}/qrcode/`;
