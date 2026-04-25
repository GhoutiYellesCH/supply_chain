import React, { useCallback, useState } from "react";
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { listSheep } from "../api";
import { useAuth } from "../auth";
import { theme } from "../theme";
import { formatDate } from "../utils";

export default function DashboardScreen({ navigation }) {
  const { user, signOut } = useAuth();
  const [sheep, setSheep] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setRefreshing(true);
    try {
      const data = await listSheep();
      setSheep(Array.isArray(data) ? data : data.results || []);
    } catch (e) {
      Alert.alert("Error", e?.response?.data?.detail || e.message);
    } finally {
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate("SheepDetails", { tagId: item.tag_id })}
    >
      <View style={styles.rowBetween}>
        <Text style={styles.tag}>{item.tag_id}</Text>
        <Text style={styles.batch}>{item.batch_number}</Text>
      </View>
      <Text style={styles.origin}>🌍 {item.origin_country}</Text>
      <Text style={styles.meta}>Imported: {item.import_date} · Created {formatDate(item.created_at)}</Text>
      {!!item.registration_tx && (
        <Text style={styles.tx} numberOfLines={1} ellipsizeMode="middle">
          tx: {item.registration_tx}
        </Text>
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.wrap}>
      <View style={styles.header}>
        <View>
          <Text style={styles.hello}>Hi, {user?.username || "guest"}</Text>
          <Text style={styles.role}>Role: {user?.role || "public"}</Text>
        </View>
        <TouchableOpacity onPress={async () => { await signOut(); navigation.replace("Login"); }}>
          <Text style={styles.logout}>Logout</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity style={styles.action} onPress={() => navigation.navigate("Scan")}>
          <Text style={styles.actionEmoji}>📷</Text>
          <Text style={styles.actionText}>Scan QR</Text>
        </TouchableOpacity>
        {user?.role === "admin" && (
          <TouchableOpacity
            style={[styles.action, { backgroundColor: theme.primary }]}
            onPress={() => navigation.navigate("RegisterSheep")}
          >
            <Text style={[styles.actionEmoji, { color: "#fff" }]}>➕</Text>
            <Text style={[styles.actionText, { color: "#fff" }]}>Register Sheep</Text>
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.sectionTitle}>All Sheep ({sheep.length})</Text>
      <FlatList
        data={sheep}
        keyExtractor={(it) => String(it.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={load} />}
        ListEmptyComponent={<Text style={styles.empty}>No sheep registered yet.</Text>}
        contentContainerStyle={{ paddingBottom: 24 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: theme.bg, padding: 16 },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 12 },
  hello: { fontSize: 18, fontWeight: "800", color: theme.text },
  role: { color: theme.muted, fontSize: 12, textTransform: "capitalize" },
  logout: { color: theme.red, fontWeight: "700" },
  actions: { flexDirection: "row", gap: 12, marginBottom: 16 },
  action: {
    flex: 1, backgroundColor: theme.card, borderRadius: 12, padding: 14,
    alignItems: "center", borderWidth: 1, borderColor: theme.border,
  },
  actionEmoji: { fontSize: 22 },
  actionText: { marginTop: 4, fontWeight: "700", color: theme.text },
  sectionTitle: { fontWeight: "800", color: theme.muted, marginBottom: 8, letterSpacing: 0.5 },
  card: {
    backgroundColor: theme.card, borderRadius: 12, padding: 14, marginBottom: 10,
    borderWidth: 1, borderColor: theme.border,
  },
  rowBetween: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  tag: { fontSize: 16, fontWeight: "800", color: theme.primary },
  batch: { color: theme.muted, fontSize: 12 },
  origin: { marginTop: 6, color: theme.text },
  meta: { marginTop: 4, color: theme.muted, fontSize: 12 },
  tx: { marginTop: 4, color: theme.muted, fontSize: 11, fontFamily: "monospace" },
  empty: { textAlign: "center", color: theme.muted, padding: 30 },
});
