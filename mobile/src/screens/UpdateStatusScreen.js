import React, { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView,
} from "react-native";
import * as Location from "expo-location";
import { addEvent } from "../api";
import { useAuth } from "../auth";
import { theme, statusColor, statusLabel } from "../theme";

const STATUS_OPTIONS_BY_ROLE = {
  admin: ["quarantine", "health_check", "transported", "delivered", "issue"],
  inspector: ["quarantine", "health_check", "issue"],
  transporter: ["transported", "delivered"],
};

export default function UpdateStatusScreen({ route, navigation }) {
  const { tagId } = route.params;
  const { user } = useAuth();
  const options = STATUS_OPTIONS_BY_ROLE[user?.role] || [];
  const [status, setStatus] = useState(options[0]);
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [coords, setCoords] = useState(null);
  const [busy, setBusy] = useState(false);

  const captureGps = async () => {
    const { status: perm } = await Location.requestForegroundPermissionsAsync();
    if (perm !== "granted") {
      Alert.alert("Permission denied", "Location permission required.");
      return;
    }
    const pos = await Location.getCurrentPositionAsync({});
    setCoords({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
  };

  const submit = async () => {
    if (!status || !location.trim()) {
      Alert.alert("Missing fields", "Status and location are required.");
      return;
    }
    setBusy(true);
    try {
      await addEvent(tagId, {
        status,
        location: location.trim(),
        notes,
        latitude: coords?.latitude,
        longitude: coords?.longitude,
      });
      Alert.alert("Success", "Event recorded and anchored.");
      navigation.goBack();
    } catch (e) {
      Alert.alert("Error", JSON.stringify(e?.response?.data || e.message));
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView style={styles.wrap} contentContainerStyle={{ padding: 16 }}>
      <Text style={styles.label}>Sheep Tag</Text>
      <Text style={styles.tag}>{tagId}</Text>

      <Text style={styles.label}>Status</Text>
      <View style={styles.statusRow}>
        {options.map((opt) => {
          const active = status === opt;
          const c = statusColor(opt);
          return (
            <TouchableOpacity
              key={opt}
              style={[
                styles.chip,
                { borderColor: c, backgroundColor: active ? c + "22" : "#fff" },
              ]}
              onPress={() => setStatus(opt)}
            >
              <Text style={{ color: c, fontWeight: "700" }}>{statusLabel(opt)}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <Text style={styles.label}>Location</Text>
      <TextInput style={styles.input} value={location} onChangeText={setLocation} placeholder="e.g. Quarantine Yard A" />

      <Text style={styles.label}>Notes</Text>
      <TextInput
        style={[styles.input, { height: 90, textAlignVertical: "top" }]}
        value={notes}
        onChangeText={setNotes}
        multiline
        placeholder="Optional"
      />

      <TouchableOpacity style={styles.gpsBtn} onPress={captureGps}>
        <Text style={styles.gpsText}>
          📍 {coords ? `GPS captured (${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)})` : "Capture GPS"}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.submit} onPress={submit} disabled={busy}>
        <Text style={styles.submitText}>{busy ? "Submitting…" : "Submit Event"}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: theme.bg },
  label: { color: theme.muted, fontSize: 12, marginTop: 14, marginBottom: 6, fontWeight: "700" },
  tag: { fontSize: 18, fontWeight: "800", color: theme.primary },
  statusRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, borderWidth: 1, marginRight: 8, marginBottom: 8 },
  input: {
    borderWidth: 1, borderColor: theme.border, borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 10, fontSize: 15, backgroundColor: "#fff",
  },
  gpsBtn: { marginTop: 16, padding: 12, borderRadius: 10, borderWidth: 1, borderColor: theme.border, alignItems: "center", backgroundColor: "#fff" },
  gpsText: { color: theme.text, fontWeight: "600" },
  submit: { backgroundColor: theme.primary, padding: 14, borderRadius: 10, alignItems: "center", marginTop: 24 },
  submitText: { color: "#fff", fontWeight: "800", fontSize: 16 },
});
