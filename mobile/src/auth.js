import React, { createContext, useContext, useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { login as apiLogin } from "./api";

const AuthContext = createContext(null);

// Heuristic fallback if backend didn't include `role` in the login response.
function roleFromUsername(u = "") {
  if (u.startsWith("admin")) return "admin";
  if (u.startsWith("inspector")) return "inspector";
  if (u.startsWith("transporter")) return "transporter";
  return "public";
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const access = await AsyncStorage.getItem("access");
      const username = await AsyncStorage.getItem("username");
      const role = await AsyncStorage.getItem("role");
      if (access && username) {
        setUser({ username, role: role || roleFromUsername(username) });
      }
      setLoading(false);
    })();
  }, []);

  const signIn = async (username, password) => {
    const data = await apiLogin(username, password);
    const role = data.role || roleFromUsername(username);
    await AsyncStorage.setItem("access", data.access);
    await AsyncStorage.setItem("refresh", data.refresh);
    await AsyncStorage.setItem("username", username);
    await AsyncStorage.setItem("role", role);
    setUser({ username, role });
  };

  const signOut = async () => {
    await AsyncStorage.multiRemove(["access", "refresh", "username", "role"]);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
