import React, { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView,
} from "react-native";
import { registerSheep } from "../api";
import { theme } from "../theme";

export default function RegisterSheepScreen({ navigation }) {
  const [origin, setOrigin] = useState("");
  const [importDate, setImportDate] = useState(new Date().toISOString().slice(0, 10));
  const [batch, setBatch] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!origin.trim() || !importDate || !batch.trim()) {
      Alert.alert("Missing fields");
      return;
    }
    setBusy(true);
    try {
      const sheep = await registerSheep({
        origin_country: origin.trim(),
        import_date: importDate,
        batch_number: batch.trim(),
      });
      Alert.alert("Sheep registered", `Tag: ${sheep.tag_id}`);
      navigation.replace("SheepDetails", { tagId: sheep.tag_id });
    } catch (e) {
      Alert.alert("Error", JSON.stringify(e?.response?.data || e.message));
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView style={styles.wrap} contentContainerStyle={{ padding: 16 }}>
      <Text style={styles.label}>Origin Country</Text>
      <TextInput style={styles.input} value={origin} onChangeText={setOrigin} placeholder="e.g. Australia" />

      <Text style={styles.label}>Import Date</Text>
      <TextInput style={styles.input} value={importDate} onChangeText={setImportDate} placeholder="YYYY-MM-DD" />

      <Text style={styles.label}>Batch Number</Text>
      <TextInput style={styles.input} value={batch} onChangeText={setBatch} placeholder="e.g. BATCH-2026-001" />

      <TouchableOpacity style={styles.submit} onPress={submit} disabled={busy}>
        <Text style={styles.submitText}>{busy ? "Registering…" : "Register & Anchor on Chain"}</Text>
      </TouchableOpacity>

      <Text style={styles.note}>
        A unique tag id and QR code will be generated automatically. The
        registration hash will be anchored on the Ethereum testnet.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: theme.bg },
  label: { color: theme.muted, fontSize: 12, marginTop: 14, marginBottom: 6, fontWeight: "700" },
  input: {
    borderWidth: 1, borderColor: theme.border, borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 10, fontSize: 15, backgroundColor: "#fff",
  },
  submit: { backgroundColor: theme.primary, padding: 14, borderRadius: 10, alignItems: "center", marginTop: 24 },
  submitText: { color: "#fff", fontWeight: "800", fontSize: 16 },
  note: { marginTop: 18, color: theme.muted, fontSize: 12, lineHeight: 18 },
});
