import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { theme, statusColor, statusLabel } from "../theme";

export default function StatusBadge({ status, size = "md" }) {
  const bg = statusColor(status);
  return (
    <View style={[styles.badge, { backgroundColor: bg + "22", borderColor: bg }, size === "sm" && styles.sm]}>
      <View style={[styles.dot, { backgroundColor: bg }]} />
      <Text style={[styles.text, { color: bg }]}>{statusLabel(status)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999,
    borderWidth: 1, alignSelf: "flex-start",
  },
  sm: { paddingHorizontal: 8, paddingVertical: 3 },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
  text: { fontSize: 12, fontWeight: "700", letterSpacing: 0.3 },
});
