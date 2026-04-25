import React, { useCallback, useState } from "react";
import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  TouchableOpacity, Image, RefreshControl, Alert,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { getSheepHistory, verifySheep, qrCodeUrl } from "../api";
import { useAuth } from "../auth";
import Timeline from "../components/Timeline";
import { theme } from "../theme";

export default function SheepDetailsScreen({ route, navigation }) {
  const { tagId } = route.params;
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [verify, setVerify] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setRefreshing(true);
    try {
      const [hist, ver] = await Promise.all([
        getSheepHistory(tagId),
        verifySheep(tagId).catch(() => null),
      ]);
      setData(hist);
      setVerify(ver);
    } catch (e) {
      Alert.alert("Error", e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [tagId]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color={theme.primary} /></View>;
  }
  if (!data) {
    return <View style={styles.center}><Text>Sheep not found.</Text></View>;
  }

  const { sheep, timeline } = data;
  const verified = verify?.verified;
  const canUpdate = user?.role === "admin" || user?.role === "inspector" || user?.role === "transporter";

  return (
    <ScrollView
      style={styles.wrap}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={load} />}
    >
      <View style={styles.headerCard}>
        <View style={styles.headerRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.tag}>{sheep.tag_id}</Text>
            <Text style={styles.origin}>🌍 {sheep.origin_country}</Text>
            <Text style={styles.meta}>Batch: {sheep.batch_number}</Text>
            <Text style={styles.meta}>Imported: {sheep.import_date}</Text>
          </View>
          <Image source={{ uri: qrCodeUrl(sheep.tag_id) }} style={styles.qr} />
        </View>

        <View style={[styles.verifyBadge, {
          backgroundColor: verified ? theme.green + "22" : theme.orange + "22",
          borderColor: verified ? theme.green : theme.orange,
        }]}>
          <Text style={[styles.verifyText, { color: verified ? theme.green : theme.orange }]}>
            {verify?.blockchain_disabled
              ? "⛓ Blockchain disabled (dev mode)"
              : verified
                ? "✓ Verified on blockchain"
                : "⚠ Not fully verified"}
          </Text>
        </View>

        {!!sheep.registration_tx && (
          <Text style={styles.tx} numberOfLines={1} ellipsizeMode="middle">
            registration tx: {sheep.registration_tx}
          </Text>
        )}
      </View>

      <Text style={styles.sectionTitle}>Lifecycle Timeline</Text>
      <Timeline events={timeline} />

      {canUpdate && (
        <TouchableOpacity
          style={styles.fab}
          onPress={() => navigation.navigate("UpdateStatus", { tagId: sheep.tag_id })}
        >
          <Text style={styles.fabText}>+ Add Event</Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: theme.bg },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  headerCard: {
    backgroundColor: theme.card, borderRadius: 16, padding: 16,
    borderWidth: 1, borderColor: theme.border, marginBottom: 16,
  },
  headerRow: { flexDirection: "row", alignItems: "flex-start" },
  tag: { fontSize: 22, fontWeight: "800", color: theme.primary },
  origin: { marginTop: 6, fontSize: 16, color: theme.text },
  meta: { color: theme.muted, marginTop: 2, fontSize: 12 },
  qr: { width: 90, height: 90, borderRadius: 8, marginLeft: 12, backgroundColor: "#fff" },
  verifyBadge: {
    marginTop: 14, padding: 10, borderRadius: 10, borderWidth: 1, alignItems: "center",
  },
  verifyText: { fontWeight: "800", letterSpacing: 0.3 },
  tx: { marginTop: 8, color: theme.muted, fontSize: 11, fontFamily: "monospace" },
  sectionTitle: { fontWeight: "800", color: theme.muted, marginBottom: 4, letterSpacing: 0.5 },
  fab: {
    backgroundColor: theme.primary, paddingVertical: 14, borderRadius: 12,
    alignItems: "center", marginTop: 8,
  },
  fabText: { color: "#fff", fontWeight: "800", fontSize: 16 },
});
