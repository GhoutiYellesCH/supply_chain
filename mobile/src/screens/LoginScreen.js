import React, { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform,
} from "react-native";
import { useAuth } from "../auth";
import { theme } from "../theme";

export default function LoginScreen({ navigation }) {
  const { signIn } = useAuth();
  const [username, setUsername] = useState("admin1");
  const [password, setPassword] = useState("password123");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    try {
      await signIn(username.trim(), password);
      navigation.replace("Dashboard");
    } catch (e) {
      Alert.alert("Login failed", e?.response?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      style={styles.wrap}
    >
      <View style={styles.brand}>
        <Text style={styles.logo}>🐑</Text>
        <Text style={styles.title}>Adhahi Tracker</Text>
        <Text style={styles.subtitle}>Blockchain-verified sheep supply chain</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Username</Text>
        <TextInput
          style={styles.input}
          autoCapitalize="none"
          value={username}
          onChangeText={setUsername}
        />
        <Text style={styles.label}>Password</Text>
        <TextInput
          style={styles.input}
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />
        <TouchableOpacity style={styles.btn} onPress={submit} disabled={busy}>
          <Text style={styles.btnText}>{busy ? "Signing in…" : "Sign in"}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate("Scan")} style={styles.linkBtn}>
          <Text style={styles.link}>Continue as public (scan QR)</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: theme.primary, justifyContent: "center", padding: 24 },
  brand: { alignItems: "center", marginBottom: 28 },
  logo: { fontSize: 64 },
  title: { color: "#fff", fontSize: 28, fontWeight: "800", marginTop: 8 },
  subtitle: { color: "#e6f4ec", marginTop: 4 },
  card: {
    backgroundColor: "#fff", borderRadius: 16, padding: 20,
    shadowColor: "#000", shadowOpacity: 0.15, shadowRadius: 12, elevation: 4,
  },
  label: { color: theme.muted, fontSize: 12, marginTop: 12, marginBottom: 4, fontWeight: "700" },
  input: {
    borderWidth: 1, borderColor: theme.border, borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 10, fontSize: 15,
  },
  btn: {
    backgroundColor: theme.primary, padding: 14, borderRadius: 10,
    alignItems: "center", marginTop: 20,
  },
  btnText: { color: "#fff", fontWeight: "800", fontSize: 16 },
  linkBtn: { alignItems: "center", marginTop: 14 },
  link: { color: theme.primary, fontWeight: "600" },
});
