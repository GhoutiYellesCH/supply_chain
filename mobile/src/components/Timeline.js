import React from "react";
import { View, Text, StyleSheet } from "react-native";
import StatusBadge from "./StatusBadge";
import { theme } from "../theme";
import { formatDate } from "../utils";

export default function Timeline({ events }) {
  if (!events?.length) {
    return <Text style={styles.empty}>No events yet.</Text>;
  }
  return (
    <View style={styles.wrap}>
      {events.map((ev, i) => {
        const last = i === events.length - 1;
        return (
          <View key={ev.id} style={styles.row}>
            <View style={styles.col}>
              <View style={styles.dot} />
              {!last && <View style={styles.line} />}
            </View>
            <View style={styles.card}>
              <View style={styles.headerRow}>
                <StatusBadge status={ev.status} size="sm" />
                {ev.on_chain_verified ? (
                  <Text style={styles.verified}>✓ on-chain</Text>
                ) : (
                  <Text style={styles.pending}>pending</Text>
                )}
              </View>
              <Text style={styles.location}>📍 {ev.location}</Text>
              {!!ev.notes && <Text style={styles.notes}>{ev.notes}</Text>}
              <Text style={styles.meta}>
                {formatDate(ev.timestamp)} · {ev.actor_username || "system"} ({ev.actor_role || "—"})
              </Text>
              {!!ev.data_hash && (
                <Text style={styles.hash} numberOfLines={1} ellipsizeMode="middle">
                  hash: {ev.data_hash}
                </Text>
              )}
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { paddingVertical: 8 },
  row: { flexDirection: "row", alignItems: "stretch" },
  col: { width: 24, alignItems: "center" },
  dot: { width: 14, height: 14, borderRadius: 7, backgroundColor: theme.primary, marginTop: 14 },
  line: { flex: 1, width: 2, backgroundColor: theme.border, marginTop: 4 },
  card: {
    flex: 1, backgroundColor: theme.card, borderRadius: 12, padding: 12,
    marginBottom: 12, marginLeft: 8,
    shadowColor: "#000", shadowOpacity: 0.05, shadowRadius: 4, elevation: 1,
    borderWidth: 1, borderColor: theme.border,
  },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  location: { marginTop: 8, fontSize: 14, color: theme.text, fontWeight: "600" },
  notes: { marginTop: 4, color: theme.muted, fontSize: 13 },
  meta: { marginTop: 6, color: theme.muted, fontSize: 12 },
  hash: { marginTop: 4, color: theme.muted, fontSize: 11, fontFamily: "monospace" },
  verified: { color: theme.green, fontSize: 12, fontWeight: "700" },
  pending: { color: theme.orange, fontSize: 12, fontWeight: "700" },
  empty: { textAlign: "center", color: theme.muted, padding: 16 },
});
